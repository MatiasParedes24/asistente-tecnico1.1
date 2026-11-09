// ==========================================================
// BACKEND GEMINI - ASISTENTE OPERATIVO
// Cloudflare Worker
//
// FUNCIONAMIENTO:
//
// 1. Recibe una pregunta natural del usuario.
// 2. Descarga base_conocimiento.json.
// 3. Genera un índice compacto de los registros.
// 4. Gemini interpreta semánticamente la pregunta.
// 5. Gemini selecciona SOLO referencias existentes.
// 6. El Worker verifica esas referencias.
// 7. Recupera la información completa desde el JSON.
// 8. Gemini redacta la respuesta usando SOLO esa información.
//
// IMPORTANTE:
// Gemini NO es la fuente de conocimiento.
// La fuente sigue siendo base_conocimiento.json.
// ==========================================================


// ==========================================================
// CONFIGURACIÓN
// ==========================================================

const MODELO_GEMINI =
    "gemini-3.5-flash-lite";


const URL_BASE_CONOCIMIENTO =
    "https://matiasparedes24.github.io/asistente-tecnico1.1/data/base_conocimiento.json";


const ORIGENES_PERMITIDOS =
    new Set([
        "https://matiasparedes24.github.io",
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ]);


const RESPUESTA_SEGURA =
    "No existe información confirmada para esta consulta en la base de conocimiento. Consulta con tu supervisor a cargo.";


// Máximo de registros que pueden utilizarse
// conjuntamente para responder una pregunta.
const MAX_REFERENCIAS_RESPUESTA =
    5;


// Máximo de opciones que se muestran cuando
// una consulta es demasiado general.
const MAX_REFERENCIAS_AMBIGUAS =
    10;


// ==========================================================
// INSTRUCCIÓN: RECUPERACIÓN SEMÁNTICA
// ==========================================================

const INSTRUCCION_SELECCION = `
Eres un recuperador semántico para una base de conocimiento
de procedimientos operativos.

Tu tarea NO es responder la pregunta del usuario.

Tu única tarea es analizar la pregunta y seleccionar las
referencias del índice que contienen información útil para
responderla.

REGLAS OBLIGATORIAS:

1. Utiliza exclusivamente el índice proporcionado.

2. No utilices conocimiento externo.

3. No inventes referencias.

4. Las referencias devueltas deben existir exactamente
   en el índice.

5. Debes comprender lenguaje natural, paráfrasis,
   sinónimos y expresiones coloquiales.

6. No es necesario que la pregunta utilice exactamente
   las mismas palabras que el índice.

Ejemplo:

"el cliente no me contesta"

puede estar relacionado con registros que contengan:

"falta de contacto"
"no contesta"
"cliente ausente"
"ciclo de llamadas"

Otro ejemplo:

"el técnico no me mandó el speedtest"

puede estar relacionado con:

"test de velocidad"
"evidencia de Speedtest"
"prueba de velocidad"

7. Si varios registros son complementarios y juntos
   permiten responder el mismo caso, utiliza:

   estado = "encontrado"

   y selecciona únicamente los registros necesarios.

8. Utiliza:

   estado = "ambiguo"

   cuando la pregunta sea demasiado general y existan
   varias alternativas operativas diferentes entre las
   cuales el usuario debe elegir.

Ejemplo:

"como valido una instalacion"

puede requerir elegir entre niveles FTTH, IPTV, ODN,
telefonía, test de velocidad, etc.

9. Utiliza:

   estado = "sin_resultado"

   únicamente cuando la base no tenga información
   suficientemente relacionada.

10. No fuerces coincidencias.

11. Para estado "encontrado":
    devuelve máximo 5 referencias.

12. Para estado "ambiguo":
    devuelve máximo 10 referencias.

Debes devolver únicamente JSON válido con esta estructura:

{
    "estado": "encontrado | ambiguo | sin_resultado",
    "refs": [
        "P:VAL001"
    ],
    "mensaje": ""
}

Las referencias comienzan por:

P: = procedimiento

C: = código de mantenimiento
`;


// ==========================================================
// INSTRUCCIÓN: GENERACIÓN DE RESPUESTA
// ==========================================================

const INSTRUCCION_RESPUESTA = `
Eres un asistente operativo para asesores de técnicos.

Debes responder utilizando EXCLUSIVAMENTE la información
autorizada proporcionada en el contexto.

REGLAS OBLIGATORIAS:

1. No utilices conocimiento externo.

2. No inventes información.

3. No inventes pasos.

4. No inventes códigos.

5. No inventes rangos.

6. No inventes aplicativos.

7. No inventes horarios.

8. No inventes motivos.

9. No inventes estados.

10. No cambies valores numéricos.

11. Puedes interpretar y redactar la información de forma
    más clara y natural.

12. Puedes combinar varios registros cuando sean
    complementarios para responder la misma situación.

13. Si los registros describen situaciones diferentes,
    debes explicar claramente cada condición.

14. Si la información depende de una condición como:

    - primera visita
    - segunda visita
    - instalación
    - mantenimiento
    - FTTH
    - HFC

    debes indicar claramente esa diferencia.

15. Responde en español.

16. La respuesta debe ser práctica, clara y orientada
    al trabajo del asesor.

17. No menciones:

    - JSON
    - prompt
    - modelo
    - recuperación semántica
    - funcionamiento interno

18. Si el contexto no permite responder la pregunta,
    responde exactamente:

"No existe información confirmada para esta consulta en la base de conocimiento. Consulta con tu supervisor a cargo."
`;


// ==========================================================
// CORS
// ==========================================================

function cabecerasCors(
    origen
) {

    if (
        !ORIGENES_PERMITIDOS.has(
            origen
        )
    ) {

        return {};
    }


    return {

        "Access-Control-Allow-Origin":
            origen,

        "Access-Control-Allow-Methods":
            "POST, OPTIONS, GET",

        "Access-Control-Allow-Headers":
            "Content-Type",

        "Vary":
            "Origin"
    };
}


// ==========================================================
// RESPUESTA JSON
// ==========================================================

function respuestaJSON(
    datos,
    estado,
    origen
) {

    return new Response(
        JSON.stringify(
            datos
        ),
        {

            status:
                estado,

            headers: {

                "Content-Type":
                    "application/json; charset=UTF-8",

                ...cabecerasCors(
                    origen
                )
            }
        }
    );
}


// ==========================================================
// SANITIZAR PREGUNTA
// ==========================================================

function sanitizarPregunta(
    texto
) {

    let limpio =
        String(
            texto || ""
        )
        .trim();


    // ------------------------------------------------------
    // ELIMINAR CORREOS
    // ------------------------------------------------------

    limpio =
        limpio.replace(
            /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi,
            "[EMAIL_OMITIDO]"
        );


    // ------------------------------------------------------
    // ELIMINAR NÚMEROS EXTENSOS
    //
    // DNI
    // teléfono
    // Customer ID
    // SOT
    // etc.
    // ------------------------------------------------------

    limpio =
        limpio.replace(
            /\b\d{7,}\b/g,
            "[DATO_OMITIDO]"
        );


    // Limitar tamaño de la pregunta.
    return limpio.slice(
        0,
        700
    );
}


// ==========================================================
// CARGAR BASE DE CONOCIMIENTO
// ==========================================================

async function cargarBase() {

    const respuesta =
        await fetch(
            URL_BASE_CONOCIMIENTO,
            {

                cache:
                    "no-store"
            }
        );


    if (
        !respuesta.ok
    ) {

        throw new Error(
            "No se pudo cargar base_conocimiento.json"
        );
    }


    return await respuesta.json();
}


// ==========================================================
// VERIFICAR REGISTRO ACTIVO
// ==========================================================

function registroActivo(
    registro
) {

    return (
        registro
            ?.control
            ?.activo
        !==
        false
    );
}


// ==========================================================
// CREAR ÍNDICE SEMÁNTICO
//
// No enviamos inicialmente todos los pasos completos.
// Solo información suficiente para que Gemini determine
// qué registros están relacionados con la pregunta.
// ==========================================================

function crearIndiceSemantico(
    base
) {

    const indice =
        [];


    // ======================================================
    // PROCEDIMIENTOS
    // ======================================================

    for (
        const procedimiento
        of (
            base.procedimientos ||
            []
        )
    ) {

        if (
            !registroActivo(
                procedimiento
            )
        ) {

            continue;
        }


        indice.push({

            ref:
                `P:${procedimiento.id}`,

            tipo:
                "procedimiento",

            id:
                procedimiento.id,

            titulo:
                procedimiento.titulo ||
                "",

            dominio:
                procedimiento.dominio ||
                "",

            tipo_sot:
                procedimiento
                    .clasificacion
                    ?.tipo_sot ||
                [],

            tecnologia:
                procedimiento
                    .clasificacion
                    ?.tecnologia ||
                [],

            aplicativos:
                procedimiento
                    .clasificacion
                    ?.aplicativos ||
                [],

            consultas_ejemplo:
                procedimiento
                    .busqueda
                    ?.consultas_ejemplo ||
                [],

            palabras_clave:
                procedimiento
                    .busqueda
                    ?.palabras_clave ||
                [],

            sinonimos:
                procedimiento
                    .busqueda
                    ?.sinonimos ||
                [],

            resumen:
                procedimiento
                    .respuesta
                    ?.resumen ||
                ""
        });
    }


    // ======================================================
    // CÓDIGOS DE MANTENIMIENTO
    // ======================================================

    for (
        const codigo
        of (
            base.codigos_mantenimiento ||
            []
        )
    ) {

        if (
            !registroActivo(
                codigo
            )
        ) {

            continue;
        }


        indice.push({

            ref:
                `C:${codigo.codigo}`,

            tipo:
                "codigo_mantenimiento",

            id:
                codigo.codigo,

            titulo:
                (
                    `${codigo.codigo} · ` +
                    `${codigo.significado || "Código de mantenimiento"}`
                ),

            categoria:
                codigo.categoria ||
                "",

            significado:
                codigo.significado ||
                "",

            detalle_adicional:
                codigo.detalle_adicional ||
                ""
        });
    }


    return indice;
}


// ==========================================================
// CREAR MAPA DEL ÍNDICE
// ==========================================================

function crearMapaIndice(
    indice
) {

    return new Map(

        indice.map(
            item => [

                String(
                    item.ref
                )
                .toUpperCase(),

                item
            ]
        )
    );
}


// ==========================================================
// RECUPERAR INFORMACIÓN COMPLETA
//
// Después de que Gemini selecciona las referencias,
// recuperamos los registros completos desde el JSON.
// ==========================================================

function recuperarRegistros(
    base,
    referencias
) {

    if (
        !Array.isArray(
            referencias
        )
    ) {

        return [];
    }


    const refs =
        new Set(

            referencias
                .map(
                    ref =>
                        String(
                            ref || ""
                        )
                        .trim()
                        .toUpperCase()
                )
                .filter(
                    Boolean
                )
        );


    const registros =
        [];


    // ======================================================
    // PROCEDIMIENTOS
    // ======================================================

    for (
        const procedimiento
        of (
            base.procedimientos ||
            []
        )
    ) {

        if (
            !registroActivo(
                procedimiento
            )
        ) {

            continue;
        }


        const ref =
            (
                "P:" +
                String(
                    procedimiento.id ||
                    ""
                )
                .toUpperCase()
            );


        if (
            !refs.has(
                ref
            )
        ) {

            continue;
        }


        registros.push({

            ref:
                ref,

            tipo:
                "procedimiento",

            id:
                procedimiento.id,

            titulo:
                procedimiento.titulo,

            dominio:
                procedimiento.dominio,

            clasificacion:
                procedimiento.clasificacion,

            respuesta:
                procedimiento.respuesta
        });
    }


    // ======================================================
    // CÓDIGOS
    // ======================================================

    for (
        const codigo
        of (
            base.codigos_mantenimiento ||
            []
        )
    ) {

        if (
            !registroActivo(
                codigo
            )
        ) {

            continue;
        }


        const ref =
            (
                "C:" +
                String(
                    codigo.codigo ||
                    ""
                )
                .toUpperCase()
            );


        if (
            !refs.has(
                ref
            )
        ) {

            continue;
        }


        registros.push({

            ref:
                ref,

            tipo:
                "codigo_mantenimiento",

            id:
                codigo.codigo,

            codigo:
                codigo.codigo,

            categoria:
                codigo.categoria,

            significado:
                codigo.significado,

            detalle_adicional:
                codigo.detalle_adicional,

            registro_sga:
                codigo.registro_sga
        });
    }


    // ======================================================
    // MANTENER ORDEN SELECCIONADO POR GEMINI
    // ======================================================

    const orden =
        new Map(

            referencias.map(
                (
                    ref,
                    indice
                ) => [

                    String(
                        ref ||
                        ""
                    )
                    .toUpperCase(),

                    indice
                ]
            )
        );


    registros.sort(
        (
            a,
            b
        ) =>

            (
                orden.get(
                    a.ref
                )
                ??
                999
            )

            -

            (
                orden.get(
                    b.ref
                )
                ??
                999
            )
    );


    return registros;
}


// ==========================================================
// EXTRAER TEXTO DE RESPUESTA GEMINI
// ==========================================================

function obtenerTextoGemini(
    datos
) {

    const partes =
        datos
            ?.candidates
            ?.[0]
            ?.content
            ?.parts
        ||
        [];


    return partes
        .map(
            parte =>
                parte.text ||
                ""
        )
        .join(
            "\n"
        )
        .trim();
}


// ==========================================================
// LLAMADA GENÉRICA A GEMINI
// ==========================================================

async function llamarGemini(
    env,
    instruccion,
    prompt,
    generationConfig = {}
) {

    let respuesta;


    try {

        respuesta =
            await fetch(

                (
                    "https://generativelanguage.googleapis.com/" +
                    `v1beta/models/${MODELO_GEMINI}:generateContent`
                ),

                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "x-goog-api-key":
                            env.GEMINI_API_KEY
                    },

                    body:
                        JSON.stringify(
                            {

                                systemInstruction: {

                                    parts: [
                                        {
                                            text:
                                                instruccion
                                        }
                                    ]
                                },

                                contents: [
                                    {

                                        role:
                                            "user",

                                        parts: [
                                            {
                                                text:
                                                    prompt
                                            }
                                        ]
                                    }
                                ],

                                generationConfig:
                                    generationConfig
                            }
                        )
                }
            );


    } catch (
        error
    ) {

        console.error(
            "Error conectando con Gemini:",
            error
        );


        throw new Error(
            "No se pudo conectar con Gemini."
        );
    }


    // ======================================================
    // LEER JSON DE RESPUESTA
    // ======================================================

    let datos;


    try {

        datos =
            await respuesta.json();


    } catch {

        throw new Error(
            "Respuesta inválida de Gemini."
        );
    }


    // ======================================================
    // ERROR DE GEMINI
    // ======================================================

    if (
        !respuesta.ok
    ) {

        console.error(
            "Gemini:",
            datos
        );


        throw new Error(

            datos
                ?.error
                ?.message

            ||

            "Gemini rechazó la solicitud."
        );
    }


    // ======================================================
    // EXTRAER TEXTO
    // ======================================================

    const texto =
        obtenerTextoGemini(
            datos
        );


    if (
        !texto
    ) {

        throw new Error(
            "Gemini no devolvió texto."
        );
    }


    return texto;
}


// ==========================================================
// LIMPIAR Y PARSEAR JSON DEVUELTO POR GEMINI
// ==========================================================

function parsearJSONGemini(
    texto
) {

    const limpio =
        String(
            texto ||
            ""
        )
        .trim()

        // Por seguridad eliminamos posibles
        // bloques Markdown.
        .replace(
            /^```json\s*/i,
            ""
        )

        .replace(
            /^```\s*/i,
            ""
        )

        .replace(
            /```$/i,
            ""
        )

        .trim();


    return JSON.parse(
        limpio
    );
}


// ==========================================================
// RECUPERACIÓN SEMÁNTICA
// ==========================================================

async function seleccionarReferencias(
    env,
    pregunta,
    indice
) {

    const prompt = `
PREGUNTA DEL ASESOR:

${pregunta}


ÍNDICE AUTORIZADO DE LA BASE DE CONOCIMIENTO:

${JSON.stringify(indice)}


Analiza semánticamente la pregunta.

Devuelve únicamente un objeto JSON con esta estructura:

{
    "estado": "encontrado | ambiguo | sin_resultado",
    "refs": [
        "P:VAL001"
    ],
    "mensaje": ""
}

No devuelvas explicaciones fuera del JSON.
`;


    const texto =
        await llamarGemini(
            env,
            INSTRUCCION_SELECCION,
            prompt,
            {

                temperature:
                    0.1,

                maxOutputTokens:
                    700,

                // Solicitamos salida JSON válida.
                responseMimeType:
                    "application/json"
            }
        );


    return parsearJSONGemini(
        texto
    );
}


// ==========================================================
// VALIDAR SELECCIÓN DE GEMINI
//
// Gemini puede sugerir referencias,
// pero el Worker comprueba que realmente existan.
// ==========================================================

function validarSeleccion(
    seleccion,
    indice
) {

    const estadosPermitidos =
        new Set([
            "encontrado",
            "ambiguo",
            "sin_resultado"
        ]);


    const estado =
        estadosPermitidos.has(
            seleccion
                ?.estado
        )

            ?

            seleccion.estado

            :

            "sin_resultado";


    const mapa =
        crearMapaIndice(
            indice
        );


    const refs =
        [];


    const vistos =
        new Set();


    for (
        const refOriginal
        of (
            seleccion
                ?.refs ||
            []
        )
    ) {

        const ref =
            String(
                refOriginal ||
                ""
            )
            .trim()
            .toUpperCase();


        // ----------------------------------------------
        // Ignorar referencias inexistentes
        // ----------------------------------------------

        if (
            !ref
            ||
            vistos.has(
                ref
            )
            ||
            !mapa.has(
                ref
            )
        ) {

            continue;
        }


        vistos.add(
            ref
        );


        refs.push(
            ref
        );
    }


    // ======================================================
    // SIN RESULTADO
    // ======================================================

    if (
        estado ===
        "sin_resultado"
    ) {

        return {

            estado:
                "sin_resultado",

            refs:
                [],

            mensaje:
                ""
        };
    }


    // Si el modelo dijo encontrado,
    // pero no devolvió referencias existentes,
    // lo tratamos como sin resultado.

    if (
        refs.length ===
        0
    ) {

        return {

            estado:
                "sin_resultado",

            refs:
                [],

            mensaje:
                ""
        };
    }


    // ======================================================
    // AMBIGUO
    // ======================================================

    if (
        estado ===
        "ambiguo"
    ) {

        // Solo una opción no es realmente ambigua.
        if (
            refs.length ===
            1
        ) {

            return {

                estado:
                    "encontrado",

                refs:
                    refs.slice(
                        0,
                        1
                    ),

                mensaje:
                    ""
            };
        }


        return {

            estado:
                "ambiguo",

            refs:
                refs.slice(
                    0,
                    MAX_REFERENCIAS_AMBIGUAS
                ),

            mensaje:
                String(
                    seleccion
                        ?.mensaje ||
                    ""
                )
                .trim()
        };
    }


    // ======================================================
    // ENCONTRADO
    // ======================================================

    return {

        estado:
            "encontrado",

        refs:
            refs.slice(
                0,
                MAX_REFERENCIAS_RESPUESTA
            ),

        mensaje:
            ""
    };
}


// ==========================================================
// CREAR OPCIONES PARA EL FRONTEND
// ==========================================================

function crearOpciones(
    indice,
    referencias
) {

    const mapa =
        crearMapaIndice(
            indice
        );


    return referencias

        .map(
            ref =>
                mapa.get(
                    String(
                        ref
                    )
                    .toUpperCase()
                )
        )

        .filter(
            Boolean
        )

        .map(
            item => ({

                ref:
                    item.ref,

                tipo:
                    item.tipo,

                id:
                    item.id,

                titulo:
                    item.titulo,

                descripcion:
                    (
                        item.resumen
                        ||
                        item.detalle_adicional
                        ||
                        item.significado
                        ||
                        ""
                    )
            })
        );
}


// ==========================================================
// GENERAR RESPUESTA FINAL
// ==========================================================

async function generarRespuesta(
    env,
    pregunta,
    registros
) {

    const contexto =
        JSON.stringify(
            registros,
            null,
            2
        );


    const prompt = `
PREGUNTA DEL ASESOR:

${pregunta}


INFORMACIÓN AUTORIZADA RECUPERADA DE LA BASE:

${contexto}


Responde exclusivamente utilizando la información anterior.

Si existen distintas condiciones dentro de los registros,
diferéncialas claramente.

No agregues información externa.
`;


    return await llamarGemini(
        env,
        INSTRUCCION_RESPUESTA,
        prompt,
        {

            temperature:
                0.2,

            maxOutputTokens:
                700
        }
    );
}


// ==========================================================
// CONSTRUIR FUENTES UTILIZADAS
// ==========================================================

function construirFuentes(
    registros
) {

    return registros.map(
        registro => ({

            ref:
                registro.ref,

            tipo:
                registro.tipo,

            id:
                registro.id,

            titulo:
                (
                    registro.titulo
                    ||
                    registro.significado
                    ||
                    registro.codigo
                    ||
                    ""
                )
        })
    );
}


// ==========================================================
// COMPATIBILIDAD CON VERSIÓN ANTERIOR
//
// Antes el frontend enviaba:
//
// {
//     pregunta: "...",
//     ids: ["VAL002"]
// }
//
// Seguimos aceptando ese formato.
// ==========================================================

function referenciasDesdeIds(
    ids
) {

    if (
        !Array.isArray(
            ids
        )
    ) {

        return [];
    }


    return ids

        .slice(
            0,
            MAX_REFERENCIAS_RESPUESTA
        )

        .map(
            id =>
                (
                    "P:" +
                    String(
                        id ||
                        ""
                    )
                    .trim()
                    .toUpperCase()
                )
        )

        .filter(
            ref =>
                ref !==
                "P:"
        );
}


// ==========================================================
// WORKER
// ==========================================================

export default {

    async fetch(
        request,
        env
    ) {

        const origen =
            request.headers.get(
                "Origin"
            )
            ||
            "";


        const url =
            new URL(
                request.url
            );


        // ==================================================
        // CORS
        // ==================================================

        if (
            request.method ===
            "OPTIONS"
        ) {

            if (
                origen
                &&
                !ORIGENES_PERMITIDOS.has(
                    origen
                )
            ) {

                return new Response(
                    null,
                    {
                        status:
                            403
                    }
                );
            }


            return new Response(
                null,
                {

                    status:
                        204,

                    headers:
                        cabecerasCors(
                            origen
                        )
                }
            );
        }


        // ==================================================
        // HEALTH CHECK
        // ==================================================

        if (
            request.method ===
            "GET"
            &&
            url.pathname ===
            "/health"
        ) {

            return respuestaJSON(
                {

                    ok:
                        true,

                    servicio:
                        "asistente-tecnico-gemini",

                    modelo:
                        MODELO_GEMINI
                },
                200,
                origen
            );
        }


        // ==================================================
        // VERIFICAR RUTA
        // ==================================================

        if (
            url.pathname !==
            "/consultar"
        ) {

            return respuestaJSON(
                {

                    ok:
                        false,

                    error:
                        "Ruta no encontrada."
                },
                404,
                origen
            );
        }


        // ==================================================
        // SOLO POST
        // ==================================================

        if (
            request.method !==
            "POST"
        ) {

            return respuestaJSON(
                {

                    ok:
                        false,

                    error:
                        "Método no permitido."
                },
                405,
                origen
            );
        }


        // ==================================================
        // VALIDAR ORIGEN
        // ==================================================

        if (
            origen
            &&
            !ORIGENES_PERMITIDOS.has(
                origen
            )
        ) {

            return respuestaJSON(
                {

                    ok:
                        false,

                    error:
                        "Origen no permitido."
                },
                403,
                origen
            );
        }


        // ==================================================
        // VERIFICAR API KEY
        // ==================================================

        if (
            !env.GEMINI_API_KEY
        ) {

            return respuestaJSON(
                {

                    ok:
                        false,

                    error:
                        "GEMINI_API_KEY no está configurada."
                },
                500,
                origen
            );
        }


        // ==================================================
        // LEER BODY
        // ==================================================

        let cuerpo;


        try {

            cuerpo =
                await request.json();


        } catch {

            return respuestaJSON(
                {

                    ok:
                        false,

                    error:
                        "Solicitud JSON inválida."
                },
                400,
                origen
            );
        }


        // ==================================================
        // PREGUNTA
        // ==================================================

        const pregunta =
            sanitizarPregunta(
                cuerpo.pregunta
            );


        if (
            !pregunta
        ) {

            return respuestaJSON(
                {

                    ok:
                        false,

                    error:
                        "La pregunta está vacía."
                },
                400,
                origen
            );
        }


        // ==================================================
        // CARGAR BASE
        // ==================================================

        let base;


        try {

            base =
                await cargarBase();


        } catch (
            error
        ) {

            console.error(
                "Base:",
                error
            );


            return respuestaJSON(
                {

                    ok:
                        false,

                    error:
                        "No se pudo consultar la base de conocimiento."
                },
                502,
                origen
            );
        }


        // ==================================================
        // CREAR ÍNDICE
        // ==================================================

        const indice =
            crearIndiceSemantico(
                base
            );


        const mapaIndice =
            crearMapaIndice(
                indice
            );


        // ==================================================
        // REFERENCIAS FORZADAS
        //
        // Se utilizan cuando:
        //
        // - el usuario seleccionó una opción
        // - frontend anterior envía IDs
        // ==================================================

        let referenciasForzadas =
            [];


        // --------------------------------------------------
        // NUEVO FORMATO:
        //
        // refs: ["P:VAL012"]
        // --------------------------------------------------

        if (
            Array.isArray(
                cuerpo.refs
            )
        ) {

            referenciasForzadas =
                cuerpo.refs

                    .map(
                        ref =>
                            String(
                                ref ||
                                ""
                            )
                            .trim()
                            .toUpperCase()
                    )

                    .filter(
                        ref =>
                            mapaIndice.has(
                                ref
                            )
                    )

                    .slice(
                        0,
                        MAX_REFERENCIAS_RESPUESTA
                    );
        }


        // --------------------------------------------------
        // FORMATO ANTIGUO:
        //
        // ids: ["VAL012"]
        // --------------------------------------------------

        else if (
            Array.isArray(
                cuerpo.ids
            )
        ) {

            referenciasForzadas =
                referenciasDesdeIds(
                    cuerpo.ids
                )

                .filter(
                    ref =>
                        mapaIndice.has(
                            ref
                        )
                );
        }


        // ==================================================
        // RECUPERACIÓN SEMÁNTICA
        // ==================================================

        let seleccion;


        // --------------------------------------------------
        // EL USUARIO YA SELECCIONÓ UNA OPCIÓN
        // --------------------------------------------------

        if (
            referenciasForzadas.length >
            0
        ) {

            seleccion = {

                estado:
                    "encontrado",

                refs:
                    referenciasForzadas,

                mensaje:
                    ""
            };
        }


        // --------------------------------------------------
        // CONSULTA NATURAL
        // --------------------------------------------------

        else {

            try {

                const seleccionGemini =
                    await seleccionarReferencias(
                        env,
                        pregunta,
                        indice
                    );


                seleccion =
                    validarSeleccion(
                        seleccionGemini,
                        indice
                    );


            } catch (
                error
            ) {

                console.error(
                    "Recuperación semántica:",
                    error
                );


                return respuestaJSON(
                    {

                        ok:
                            false,

                        tipo:
                            "error",

                        error:
                            "No se pudo interpretar la consulta con el recuperador semántico."
                    },
                    502,
                    origen
                );
            }
        }


        // ==================================================
        // SIN RESULTADO
        // ==================================================

        if (
            seleccion.estado ===
            "sin_resultado"
        ) {

            return respuestaJSON(
                {

                    ok:
                        true,

                    tipo:
                        "sin_resultado",

                    respuesta:
                        RESPUESTA_SEGURA,

                    modelo:
                        MODELO_GEMINI,

                    fuentes_usadas:
                        []
                },
                200,
                origen
            );
        }


        // ==================================================
        // CONSULTA AMBIGUA
        // ==================================================

        if (
            seleccion.estado ===
            "ambiguo"
        ) {

            const opciones =
                crearOpciones(
                    indice,
                    seleccion.refs
                );


            return respuestaJSON(
                {

                    ok:
                        true,

                    tipo:
                        "ambigua",

                    respuesta:
                        (
                            seleccion.mensaje
                            ||
                            "Encontré varias opciones relacionadas. Selecciona la que deseas consultar."
                        ),

                    opciones:
                        opciones,

                    modelo:
                        MODELO_GEMINI,

                    fuentes_usadas:
                        []
                },
                200,
                origen
            );
        }


        // ==================================================
        // RECUPERAR INFORMACIÓN COMPLETA
        // ==================================================

        const registros =
            recuperarRegistros(
                base,
                seleccion.refs
            );


        if (
            registros.length ===
            0
        ) {

            return respuestaJSON(
                {

                    ok:
                        true,

                    tipo:
                        "sin_resultado",

                    respuesta:
                        RESPUESTA_SEGURA,

                    modelo:
                        MODELO_GEMINI,

                    fuentes_usadas:
                        []
                },
                200,
                origen
            );
        }


        // ==================================================
        // GENERAR RESPUESTA FINAL
        // ==================================================

        let textoRespuesta;


        try {

            textoRespuesta =
                await generarRespuesta(
                    env,
                    pregunta,
                    registros
                );


        } catch (
            error
        ) {

            console.error(
                "Generación final:",
                error
            );


            return respuestaJSON(
                {

                    ok:
                        false,

                    tipo:
                        "error",

                    error:
                        "No se pudo generar la respuesta final."
                },
                502,
                origen
            );
        }


        // ==================================================
        // FUENTES UTILIZADAS
        // ==================================================

        const fuentes =
            construirFuentes(
                registros
            );


        // ==================================================
        // RESPUESTA FINAL AL FRONTEND
        // ==================================================

        return respuestaJSON(
            {

                ok:
                    true,

                tipo:
                    "respuesta",

                respuesta:
                    textoRespuesta,

                modelo:
                    MODELO_GEMINI,

                fuentes_usadas:
                    fuentes,

                procedimientos_usados:
                    fuentes

                        .filter(
                            fuente =>
                                fuente.tipo ===
                                "procedimiento"
                        )

                        .map(
                            fuente =>
                                fuente.id
                        ),

                codigos_usados:
                    fuentes

                        .filter(
                            fuente =>
                                fuente.tipo ===
                                "codigo_mantenimiento"
                        )

                        .map(
                            fuente =>
                                fuente.id
                        )
            },
            200,
            origen
        );
    }
};