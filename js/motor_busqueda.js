// ==========================================================
// MOTOR DE BÚSQUEDA - ASISTENTE TÉCNICO
// Versión web equivalente al motor_busqueda.py
// ==========================================================


// ==========================================================
// CONFIGURACIÓN
// ==========================================================

const RUTA_BASE_CONOCIMIENTO = "data/base_conocimiento.json";

const UMBRAL_RESPUESTA = 10.0;
const UMBRAL_ALTA = 20.0;
const UMBRAL_MEDIA = 14.0;
const MAX_RESULTADOS = 5;


// ==========================================================
// STOPWORDS
// ==========================================================

const STOPWORDS = new Set([
    "a",
    "al",
    "algo",
    "como",
    "con",
    "cual",
    "cuales",
    "cuando",
    "de",
    "del",
    "donde",
    "el",
    "ella",
    "en",
    "es",
    "esta",
    "este",
    "esto",
    "hacer",
    "hay",
    "la",
    "las",
    "lo",
    "los",
    "me",
    "mi",
    "para",
    "por",
    "que",
    "se",
    "si",
    "su",
    "un",
    "una",
    "y",
    "o"
]);


// ==========================================================
// VARIABLES GLOBALES
// ==========================================================

let BASE_CONOCIMIENTO = null;


// ==========================================================
// CARGAR BASE DE CONOCIMIENTO
// ==========================================================

async function cargarBaseConocimiento() {

    try {

        const respuesta = await fetch(
            RUTA_BASE_CONOCIMIENTO,
            {
                cache: "no-store"
            }
        );

        if (!respuesta.ok) {

            throw new Error(
                `No se pudo cargar la base de conocimiento. ` +
                `Código HTTP: ${respuesta.status}`
            );
        }

        BASE_CONOCIMIENTO = await respuesta.json();

        console.log(
            "Base de conocimiento cargada correctamente."
        );

        console.log(
            "Procedimientos:",
            BASE_CONOCIMIENTO.procedimientos?.length || 0
        );

        console.log(
            "Códigos de mantenimiento:",
            BASE_CONOCIMIENTO.codigos_mantenimiento?.length || 0
        );

        return BASE_CONOCIMIENTO;

    } catch (error) {

        console.error(
            "Error cargando base_conocimiento.json:",
            error
        );

        BASE_CONOCIMIENTO = null;

        throw error;
    }
}


// ==========================================================
// NORMALIZACIÓN DE TEXTO
// ==========================================================

function normalizarTexto(texto) {

    if (
        texto === null ||
        texto === undefined
    ) {
        return "";
    }

    return String(texto)
        .toLowerCase()
        .normalize("NFD")
        .replace(
            /[\u0300-\u036f]/g,
            ""
        )
        .replace(
            /[^a-z0-9\s]/g,
            " "
        )
        .replace(
            /\s+/g,
            " "
        )
        .trim();
}


// ==========================================================
// TOKENIZAR
// ==========================================================

function tokenizar(texto) {

    const textoNormalizado = normalizarTexto(
        texto
    );

    if (!textoNormalizado) {
        return [];
    }

    return textoNormalizado
        .split(" ")
        .filter(
            palabra =>
                palabra.length >= 3 &&
                !STOPWORDS.has(palabra)
        );
}


// ==========================================================
// EXTRAER CÓDIGOS
// ==========================================================

function extraerCodigos(texto) {

    const coincidencias = String(
        texto || ""
    ).match(
        /\b[A-Za-z]{2}\d{2}\b/g
    );

    if (!coincidencias) {
        return [];
    }

    return coincidencias.map(
        codigo => codigo.toUpperCase()
    );
}


// ==========================================================
// BUSCAR CÓDIGO DE MANTENIMIENTO
// ==========================================================

function buscarCodigoMantenimiento(
    pregunta,
    base
) {

    const codigosPregunta = extraerCodigos(
        pregunta
    );

    if (
        codigosPregunta.length === 0
    ) {

        return null;
    }

    const catalogo = new Map();

    const codigosBase =
        base.codigos_mantenimiento || [];

    for (
        const registro
        of codigosBase
    ) {

        const control =
            registro.control || {};

        if (
            control.activo === false
        ) {
            continue;
        }

        const codigo = String(
            registro.codigo || ""
        )
            .trim()
            .toUpperCase();

        if (codigo) {

            catalogo.set(
                codigo,
                registro
            );
        }
    }

    for (
        const codigo
        of codigosPregunta
    ) {

        if (
            catalogo.has(codigo)
        ) {

            return catalogo.get(
                codigo
            );
        }
    }

    return null;
}


// ==========================================================
// CONSTRUIR RESPUESTA DE CÓDIGO
// ==========================================================

function construirRespuestaCodigo(
    registro
) {

    const codigo =
        registro.codigo || "";

    const categoria =
        registro.categoria || "";

    const significado =
        registro.significado || "";

    const detalleAdicional =
        registro.detalle_adicional || "";

    const registroSGA =
        registro.registro_sga || "";

    const lineas = [
        "CÓDIGO DE MANTENIMIENTO",
        "",
        `Código: ${codigo}`,
        `Categoría: ${categoria}`,
        `Significado: ${significado}`
    ];

    if (detalleAdicional) {

        lineas.push(
            `Detalle adicional: ${detalleAdicional}`
        );
    }

    if (registroSGA) {

        lineas.push("");
        lineas.push(
            `Registro SGA: ${registroSGA}`
        );
    }

    return lineas.join("\n");
}


// ==========================================================
// SIMILITUD DE TEXTO
// ==========================================================

function similitudTexto(
    textoA,
    textoB
) {

    const a = normalizarTexto(
        textoA
    );

    const b = normalizarTexto(
        textoB
    );

    if (
        !a ||
        !b
    ) {
        return 0;
    }

    if (a === b) {
        return 1;
    }

    const matriz = [];

    for (
        let i = 0;
        i <= b.length;
        i++
    ) {

        matriz[i] = [i];
    }

    for (
        let j = 0;
        j <= a.length;
        j++
    ) {

        matriz[0][j] = j;
    }

    for (
        let i = 1;
        i <= b.length;
        i++
    ) {

        for (
            let j = 1;
            j <= a.length;
            j++
        ) {

            if (
                b.charAt(i - 1) ===
                a.charAt(j - 1)
            ) {

                matriz[i][j] =
                    matriz[i - 1][j - 1];

            } else {

                matriz[i][j] =
                    Math.min(
                        matriz[i - 1][j - 1] + 1,
                        matriz[i][j - 1] + 1,
                        matriz[i - 1][j] + 1
                    );
            }
        }
    }

    const distancia =
        matriz[b.length][a.length];

    const longitudMaxima =
        Math.max(
            a.length,
            b.length
        );

    if (
        longitudMaxima === 0
    ) {
        return 1;
    }

    return (
        1 -
        distancia /
        longitudMaxima
    );
}


// ==========================================================
// OBTENER TEXTOS DEL PROCEDIMIENTO
// ==========================================================

function obtenerTextosBusqueda(
    procedimiento
) {

    const textos = [];

    textos.push({
        campo: "titulo",
        texto:
            procedimiento.titulo || "",
        peso: 8.0
    });

    textos.push({
        campo: "dominio",
        texto:
            procedimiento.dominio || "",
        peso: 2.0
    });

    const busqueda =
        procedimiento.busqueda || {};

    const consultasEjemplo =
        busqueda.consultas_ejemplo || [];

    const palabrasClave =
        busqueda.palabras_clave || [];

    const sinonimos =
        busqueda.sinonimos || [];

    for (
        const consulta
        of consultasEjemplo
    ) {

        textos.push({
            campo:
                "consulta_ejemplo",

            texto:
                consulta,

            peso:
                7.0
        });
    }

    for (
        const palabra
        of palabrasClave
    ) {

        textos.push({
            campo:
                "palabra_clave",

            texto:
                palabra,

            peso:
                5.0
        });
    }

    for (
        const sinonimo
        of sinonimos
    ) {

        textos.push({
            campo:
                "sinonimo",

            texto:
                sinonimo,

            peso:
                5.0
        });
    }

    const clasificacion =
        procedimiento.clasificacion || {};

    const tiposSot =
        clasificacion.tipo_sot || [];

    const tecnologias =
        clasificacion.tecnologia || [];

    const aplicativos =
        clasificacion.aplicativos || [];

    for (
        const tipo
        of tiposSot
    ) {

        textos.push({
            campo:
                "tipo_sot",

            texto:
                tipo,

            peso:
                3.0
        });
    }

    for (
        const tecnologia
        of tecnologias
    ) {

        textos.push({
            campo:
                "tecnologia",

            texto:
                tecnologia,

            peso:
                3.0
        });
    }

    for (
        const aplicativo
        of aplicativos
    ) {

        textos.push({
            campo:
                "aplicativo",

            texto:
                aplicativo,

            peso:
                3.0
        });
    }

    return textos;
}


// ==========================================================
// INTERSECCIÓN DE TOKENS
// ==========================================================

function contarTokensComunes(
    tokensPregunta,
    tokensTexto
) {

    const conjuntoPregunta =
        new Set(tokensPregunta);

    const conjuntoTexto =
        new Set(tokensTexto);

    let cantidad = 0;

    for (
        const token
        of conjuntoPregunta
    ) {

        if (
            conjuntoTexto.has(token)
        ) {

            cantidad++;
        }
    }

    return cantidad;
}


// ==========================================================
// EVIDENCIA LÉXICA
// ==========================================================

function evaluarEvidenciaLexica(
    pregunta,
    procedimiento
) {

    const tokensPregunta =
        tokenizar(pregunta);

    if (
        tokensPregunta.length < 2
    ) {

        return {
            valida: false,
            maxComunes: 0,
            fraseFuerte: false
        };
    }

    let maxComunes = 0;
    let fraseFuerte = false;

    const preguntaNormalizada =
        normalizarTexto(
            pregunta
        );

    const textos =
        obtenerTextosBusqueda(
            procedimiento
        );

    for (
        const item
        of textos
    ) {

        const textoNormalizado =
            normalizarTexto(
                item.texto
            );

        if (
            !textoNormalizado
        ) {
            continue;
        }

        const tokensTexto =
            tokenizar(
                item.texto
            );

        const comunes =
            contarTokensComunes(
                tokensPregunta,
                tokensTexto
            );

        maxComunes =
            Math.max(
                maxComunes,
                comunes
            );

        const camposFuertes =
            [
                "titulo",
                "consulta_ejemplo",
                "palabra_clave",
                "sinonimo"
            ];

        if (
            textoNormalizado.length >= 5 &&
            (
                preguntaNormalizada.includes(
                    textoNormalizado
                ) ||
                textoNormalizado.includes(
                    preguntaNormalizada
                )
            ) &&
            camposFuertes.includes(
                item.campo
            )
        ) {

            fraseFuerte = true;
        }
    }

    return {
        valida:
            fraseFuerte ||
            maxComunes >= 2,

        maxComunes:
            maxComunes,

        fraseFuerte:
            fraseFuerte
    };
}


// ==========================================================
// PUNTUAR PROCEDIMIENTO
// ==========================================================

function puntuarProcedimiento(
    pregunta,
    procedimiento
) {

    const evidencia =
        evaluarEvidenciaLexica(
            pregunta,
            procedimiento
        );

    if (
        !evidencia.valida
    ) {

        return {
            puntuacion: 0,
            razones: []
        };
    }

    const preguntaNormalizada =
        normalizarTexto(
            pregunta
        );

    const tokensPregunta =
        tokenizar(
            pregunta
        );

    let puntuacion = 0;

    const razones = [];

    const textos =
        obtenerTextosBusqueda(
            procedimiento
        );

    for (
        const item
        of textos
    ) {

        const textoNormalizado =
            normalizarTexto(
                item.texto
            );

        if (
            !textoNormalizado
        ) {
            continue;
        }

        const tokensTexto =
            tokenizar(
                item.texto
            );

        const cantidadComunes =
            contarTokensComunes(
                tokensPregunta,
                tokensTexto
            );

        let puntos = 0;

        // --------------------------------------------------
        // COINCIDENCIA EXACTA
        // --------------------------------------------------

        if (
            textoNormalizado ===
            preguntaNormalizada
        ) {

            puntos +=
                item.peso +
                8.0;
        }

        // --------------------------------------------------
        // TEXTO GUARDADO DENTRO DE LA PREGUNTA
        // --------------------------------------------------

        else if (
            textoNormalizado.length >= 5 &&
            preguntaNormalizada.includes(
                textoNormalizado
            )
        ) {

            puntos +=
                item.peso +
                5.0;
        }

        // --------------------------------------------------
        // PREGUNTA DENTRO DEL TEXTO GUARDADO
        // --------------------------------------------------

        else if (
            preguntaNormalizada.length >= 5 &&
            textoNormalizado.includes(
                preguntaNormalizada
            )
        ) {

            puntos +=
                item.peso *
                0.8;
        }

        // --------------------------------------------------
        // TOKENS EN COMÚN
        // --------------------------------------------------

        if (
            cantidadComunes > 0
        ) {

            const cobertura =
                cantidadComunes /
                Math.max(
                    tokensPregunta.length,
                    1
                );

            puntos +=
                cobertura *
                item.peso;

            if (
                cantidadComunes >= 2
            ) {

                puntos +=
                    Math.min(
                        3.0,
                        cantidadComunes *
                        0.8
                    );
            }
        }

        // --------------------------------------------------
        // SIMILITUD DIFUSA
        // --------------------------------------------------

        if (
            cantidadComunes > 0 ||
            evidencia.fraseFuerte
        ) {

            const similitud =
                similitudTexto(
                    pregunta,
                    item.texto
                );

            if (
                similitud >= 0.55
            ) {

                puntos +=
                    similitud *
                    item.peso *
                    0.4;
            }
        }

        if (
            puntos > 0
        ) {

            puntuacion += puntos;

            razones.push({
                campo:
                    item.campo,

                valor:
                    item.texto,

                puntos:
                    Number(
                        puntos.toFixed(2)
                    )
            });
        }
    }

    if (
        evidencia.maxComunes < 2 &&
        !evidencia.fraseFuerte
    ) {

        return {
            puntuacion: 0,
            razones: []
        };
    }

    return {
        puntuacion:
            Number(
                puntuacion.toFixed(2)
            ),

        razones:
            razones
    };
}


// ==========================================================
// CONSTRUIR RESPUESTA DEL PROCEDIMIENTO
// ==========================================================

function construirRespuestaProcedimiento(
    procedimiento
) {

    const respuesta =
        procedimiento.respuesta || {};

    const lineas = [
        `PROCEDIMIENTO: ${procedimiento.titulo || ""}`
    ];

    const resumen =
        respuesta.resumen || "";

    if (resumen) {

        lineas.push("");
        lineas.push(
            resumen
        );
    }

    // ------------------------------------------------------
    // PASOS
    // ------------------------------------------------------

    const pasos =
        respuesta.pasos || [];

    if (
        pasos.length > 0
    ) {

        lineas.push("");
        lineas.push(
            "PASOS:"
        );

        const pasosOrdenados =
            [...pasos].sort(
                (
                    a,
                    b
                ) =>
                    (
                        a.orden || 0
                    )
                    -
                    (
                        b.orden || 0
                    )
            );

        for (
            const paso
            of pasosOrdenados
        ) {

            const orden =
                paso.orden || "";

            const aplicativo =
                paso.aplicativo || "";

            const accion =
                paso.accion || "";

            let textoPaso =
                `${orden}. `;

            if (
                aplicativo
            ) {

                textoPaso +=
                    `[${aplicativo}] `;
            }

            textoPaso += accion;

            lineas.push(
                textoPaso
            );

            if (
                paso.validacion
            ) {

                lineas.push(
                    `   Verificar: ${paso.validacion}`
                );
            }

            if (
                paso.si_no_cumple
            ) {

                lineas.push(
                    `   Si no cumple: ${paso.si_no_cumple}`
                );
            }
        }
    }

    // ------------------------------------------------------
    // PRECONDICIONES
    // ------------------------------------------------------

    const precondiciones =
        respuesta.precondiciones || [];

    if (
        precondiciones.length > 0
    ) {

        lineas.push("");
        lineas.push(
            "PRECONDICIONES:"
        );

        for (
            const item
            of precondiciones
        ) {

            lineas.push(
                `- ${item}`
            );
        }
    }

    // ------------------------------------------------------
    // VERIFICACIONES
    // ------------------------------------------------------

    const verificaciones =
        respuesta.verificaciones || [];

    if (
        verificaciones.length > 0
    ) {

        lineas.push("");
        lineas.push(
            "VERIFICAR:"
        );

        for (
            const item
            of verificaciones
        ) {

            lineas.push(
                `- ${item}`
            );
        }
    }

    // ------------------------------------------------------
    // ADVERTENCIAS
    // ------------------------------------------------------

    const advertencias =
        respuesta.advertencias || [];

    if (
        advertencias.length > 0
    ) {

        lineas.push("");
        lineas.push(
            "ADVERTENCIAS:"
        );

        for (
            const item
            of advertencias
        ) {

            lineas.push(
                `- ${item}`
            );
        }
    }

    // ------------------------------------------------------
    // ACCIÓN SI NO CUMPLE
    // ------------------------------------------------------

    const accionSiNoCumple =
        respuesta.accion_si_no_cumple || "";

    if (
        accionSiNoCumple
    ) {

        lineas.push("");
        lineas.push(
            "SI NO CUMPLE:"
        );

        lineas.push(
            accionSiNoCumple
        );
    }

    // ------------------------------------------------------
    // ESCALAMIENTO
    // ------------------------------------------------------

    const escalamiento =
        respuesta.escalamiento || "";

    if (
        escalamiento
    ) {

        lineas.push("");
        lineas.push(
            "ESCALAMIENTO:"
        );

        lineas.push(
            escalamiento
        );
    }

    return lineas.join("\n");
}


// ==========================================================
// BUSCAR PROCEDIMIENTOS
// ==========================================================

function buscarProcedimientos(
    pregunta,
    base
) {

    const resultados = [];

    const procedimientos =
        base.procedimientos || [];

    for (
        const procedimiento
        of procedimientos
    ) {

        const control =
            procedimiento.control || {};

        if (
            control.activo === false
        ) {

            continue;
        }

        const evaluacion =
            puntuarProcedimiento(
                pregunta,
                procedimiento
            );

        const puntuacion =
            evaluacion.puntuacion;

        if (
            puntuacion <
            UMBRAL_RESPUESTA
        ) {

            continue;
        }

        let confianza =
            "BAJA";

        if (
            puntuacion >=
            UMBRAL_ALTA
        ) {

            confianza =
                "ALTA";

        } else if (
            puntuacion >=
            UMBRAL_MEDIA
        ) {

            confianza =
                "MEDIA";
        }

        resultados.push({
            procedimiento:
                procedimiento,

            puntuacion:
                puntuacion,

            confianza:
                confianza,

            razones:
                evaluacion.razones
        });
    }

    resultados.sort(
        (
            a,
            b
        ) =>
            b.puntuacion -
            a.puntuacion
    );

    return resultados.slice(
        0,
        MAX_RESULTADOS
    );
}


// ==========================================================
// CONSULTA PRINCIPAL
// ==========================================================

function consultar(
    pregunta
) {

    if (
        !BASE_CONOCIMIENTO
    ) {

        return {
            tipo:
                "error",

            confianza:
                "NINGUNA",

            respuesta:
                "La base de conocimiento todavía no ha sido cargada.",

            resultados:
                []
        };
    }

    const configuracion =
        BASE_CONOCIMIENTO.configuracion || {};

    const respuestaSinResultado =
        configuracion.respuesta_sin_resultado ||
        (
            "No existe información confirmada para esta consulta " +
            "en la base de conocimiento. " +
            "Consulta con tu supervisor a cargo."
        );

    const preguntaLimpia =
        String(
            pregunta || ""
        ).trim();

    if (
        !preguntaLimpia
    ) {

        return {
            tipo:
                "sin_resultado",

            confianza:
                "NINGUNA",

            respuesta:
                respuestaSinResultado,

            resultados:
                []
        };
    }

    // ======================================================
    // 1. BUSCAR CÓDIGO DE MANTENIMIENTO
    // ======================================================

    const codigo =
        buscarCodigoMantenimiento(
            preguntaLimpia,
            BASE_CONOCIMIENTO
        );

    if (
        codigo
    ) {

        return {
            tipo:
                "codigo",

            confianza:
                "ALTA",

            respuesta:
                construirRespuestaCodigo(
                    codigo
                ),

            codigo:
                codigo,

            resultados:
                [codigo]
        };
    }

    // ======================================================
    // 2. SI ESCRIBIÓ UN CÓDIGO QUE NO EXISTE
    // ======================================================

    const codigosEscritos =
        extraerCodigos(
            preguntaLimpia
        );

    if (
        codigosEscritos.length > 0
    ) {

        return {
            tipo:
                "sin_resultado",

            confianza:
                "NINGUNA",

            respuesta:
                (
                    `El código ${codigosEscritos[0]} ` +
                    `no existe en el catálogo de mantenimiento registrado. ` +
                    `Consulta con tu supervisor a cargo.`
                ),

            resultados:
                []
        };
    }

    // ======================================================
    // 3. EVITAR PREGUNTAS DEMASIADO CORTAS
    // ======================================================

    const tokensPregunta =
        tokenizar(
            preguntaLimpia
        );

    if (
        tokensPregunta.length < 2
    ) {

        return {
            tipo:
                "sin_resultado",

            confianza:
                "NINGUNA",

            respuesta:
                respuestaSinResultado,

            resultados:
                []
        };
    }

    // ======================================================
    // 4. BUSCAR PROCEDIMIENTOS
    // ======================================================

    const resultados =
        buscarProcedimientos(
            preguntaLimpia,
            BASE_CONOCIMIENTO
        );

    if (
        resultados.length === 0
    ) {

        return {
            tipo:
                "sin_resultado",

            confianza:
                "NINGUNA",

            respuesta:
                respuestaSinResultado,

            resultados:
                []
        };
    }

    // ======================================================
    // 5. TOMAR MEJOR RESULTADO
    // ======================================================

    const mejor =
        resultados[0];

    return {
        tipo:
            "procedimiento",

        confianza:
            mejor.confianza,

        respuesta:
            construirRespuestaProcedimiento(
                mejor.procedimiento
            ),

        procedimiento:
            mejor.procedimiento,

        puntuacion:
            mejor.puntuacion,

        razones:
            mejor.razones,

        resultados:
            resultados
    };
}


// ==========================================================
// INICIALIZAR MOTOR
// ==========================================================

async function inicializarMotor() {

    try {

        await cargarBaseConocimiento();

        return {
            ok: true,
            mensaje:
                "Motor inicializado correctamente."
        };

    } catch (error) {

        return {
            ok: false,
            mensaje:
                (
                    "No se pudo cargar la base de conocimiento."
                ),
            error:
                error
        };
    }
}


// ==========================================================
// EXPONER FUNCIONES PARA EL HTML
// ==========================================================

window.AsistenteMotor = {

    inicializar:
        inicializarMotor,

    consultar:
        consultar,

    cargarBaseConocimiento:
        cargarBaseConocimiento,

    normalizarTexto:
        normalizarTexto,

    tokenizar:
        tokenizar,

    extraerCodigos:
        extraerCodigos,

    buscarCodigoMantenimiento:
        buscarCodigoMantenimiento
};