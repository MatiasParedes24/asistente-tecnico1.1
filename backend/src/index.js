// ==========================================================
// BACKEND GEMINI - ASISTENTE OPERATIVO
// Cloudflare Worker
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


// ==========================================================
// INSTRUCCIÓN PARA GEMINI
// ==========================================================

const INSTRUCCION_SISTEMA = `
Eres un asistente de apoyo para asesores de soporte técnico.

REGLAS OBLIGATORIAS:

- Utiliza exclusivamente el contexto autorizado proporcionado.
- No uses conocimiento externo para completar procedimientos.
- No inventes pasos, códigos, rangos, aplicativos, horarios,
  estados o reglas.
- No cambies valores numéricos.
- Puedes redactar la respuesta de forma más clara y natural.
- Sé breve y operativo.
- Si el contexto no permite responder, responde exactamente:

"No existe información confirmada para esta consulta en la base
de conocimiento. Consulta con tu supervisor a cargo."
`;


// ==========================================================
// CORS
// ==========================================================

function cabecerasCors(origen) {

    if (
        !ORIGENES_PERMITIDOS.has(origen)
    ) {
        return {};
    }

    return {
        "Access-Control-Allow-Origin": origen,
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Vary": "Origin"
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
        JSON.stringify(datos),
        {
            status: estado,

            headers: {
                "Content-Type":
                    "application/json; charset=UTF-8",

                ...cabecerasCors(origen)
            }
        }
    );
}


// ==========================================================
// SANITIZAR PREGUNTA
// ==========================================================

function sanitizarPregunta(texto) {

    let limpio =
        String(texto || "")
            .trim();

    // Correos
    limpio =
        limpio.replace(
            /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi,
            "[EMAIL_OMITIDO]"
        );

    // DNI, teléfonos, Customer ID,
    // SOT u otros números extensos
    limpio =
        limpio.replace(
            /\b\d{7,}\b/g,
            "[DATO_OMITIDO]"
        );

    return limpio.slice(
        0,
        700
    );
}


// ==========================================================
// CARGAR BASE PUBLICADA
// ==========================================================

async function cargarBase() {

    const respuesta =
        await fetch(
            URL_BASE_CONOCIMIENTO
        );

    if (!respuesta.ok) {

        throw new Error(
            "No se pudo cargar base_conocimiento.json"
        );
    }

    return await respuesta.json();
}


// ==========================================================
// RECUPERAR PROCEDIMIENTOS POR ID
// ==========================================================

function recuperarProcedimientos(
    base,
    ids
) {

    if (
        !Array.isArray(ids)
    ) {
        return [];
    }

    const permitidos =
        ids
            .slice(0, 3)
            .map(
                id =>
                    String(id)
                        .trim()
                        .toUpperCase()
            );

    return (
        base.procedimientos || []
    )
        .filter(
            procedimiento =>
                procedimiento
                    .control
                    ?.activo !== false
                &&
                permitidos.includes(
                    String(
                        procedimiento.id || ""
                    ).toUpperCase()
                )
        )
        .map(
            procedimiento => ({

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
            })
        );
}


// ==========================================================
// EXTRAER TEXTO DE GEMINI
// ==========================================================

function obtenerTextoGemini(datos) {

    const partes =
        datos
            ?.candidates
            ?.[0]
            ?.content
            ?.parts || [];

    return partes
        .map(
            parte =>
                parte.text || ""
        )
        .join("\n")
        .trim();
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
            ) || "";


        // --------------------------------------------------
        // CORS
        // --------------------------------------------------

        if (
            request.method ===
            "OPTIONS"
        ) {

            if (
                !ORIGENES_PERMITIDOS.has(
                    origen
                )
            ) {

                return new Response(
                    null,
                    {
                        status: 403
                    }
                );
            }

            return new Response(
                null,
                {
                    status: 204,

                    headers:
                        cabecerasCors(
                            origen
                        )
                }
            );
        }


        // --------------------------------------------------
        // RUTA
        // --------------------------------------------------

        const url =
            new URL(
                request.url
            );

        if (
            url.pathname !==
            "/consultar"
        ) {

            return respuestaJSON(
                {
                    ok: false,
                    error:
                        "Ruta no encontrada."
                },
                404,
                origen
            );
        }


        if (
            request.method !==
            "POST"
        ) {

            return respuestaJSON(
                {
                    ok: false,
                    error:
                        "Método no permitido."
                },
                405,
                origen
            );
        }


        // --------------------------------------------------
        // CLAVE GEMINI
        // --------------------------------------------------

        if (
            !env.GEMINI_API_KEY
        ) {

            return respuestaJSON(
                {
                    ok: false,
                    error:
                        "GEMINI_API_KEY no está configurada."
                },
                500,
                origen
            );
        }


        // --------------------------------------------------
        // LEER DATOS
        // --------------------------------------------------

        let cuerpo;

        try {

            cuerpo =
                await request.json();

        } catch {

            return respuestaJSON(
                {
                    ok: false,
                    error:
                        "Solicitud JSON inválida."
                },
                400,
                origen
            );
        }


        const pregunta =
            sanitizarPregunta(
                cuerpo.pregunta
            );

        const ids =
            Array.isArray(
                cuerpo.ids
            )
                ? cuerpo.ids
                : [];


        if (!pregunta) {

            return respuestaJSON(
                {
                    ok: false,
                    error:
                        "La pregunta está vacía."
                },
                400,
                origen
            );
        }


        if (
            ids.length === 0
        ) {

            return respuestaJSON(
                {
                    ok: true,
                    respuesta:
                        RESPUESTA_SEGURA
                },
                200,
                origen
            );
        }


        // --------------------------------------------------
        // CARGAR INFORMACIÓN AUTORIZADA
        // --------------------------------------------------

        let base;

        try {

            base =
                await cargarBase();

        } catch (error) {

            console.error(error);

            return respuestaJSON(
                {
                    ok: false,
                    error:
                        "No se pudo consultar la base de conocimiento."
                },
                502,
                origen
            );
        }


        const procedimientos =
            recuperarProcedimientos(
                base,
                ids
            );


        if (
            procedimientos.length === 0
        ) {

            return respuestaJSON(
                {
                    ok: true,
                    respuesta:
                        RESPUESTA_SEGURA
                },
                200,
                origen
            );
        }


        // --------------------------------------------------
        // CONTEXTO
        // --------------------------------------------------

        const contexto =
            JSON.stringify(
                procedimientos,
                null,
                2
            );


        const prompt = `
PREGUNTA DEL ASESOR:

${pregunta}


INFORMACIÓN AUTORIZADA DE LA BASE DE CONOCIMIENTO:

${contexto}


Responde exclusivamente utilizando la información anterior.
`;


        // --------------------------------------------------
        // GEMINI
        // --------------------------------------------------

        let respuestaGemini;

        try {

            respuestaGemini =
                await fetch(
                    `https://generativelanguage.googleapis.com/v1beta/models/${MODELO_GEMINI}:generateContent`,
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
                                                    INSTRUCCION_SISTEMA
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

                                    generationConfig: {
                                        maxOutputTokens:
                                            600
                                    }
                                }
                            )
                    }
                );

        } catch (error) {

            console.error(error);

            return respuestaJSON(
                {
                    ok: false,
                    error:
                        "No se pudo conectar con Gemini."
                },
                502,
                origen
            );
        }


        let datos;

        try {

            datos =
                await respuestaGemini.json();

        } catch {

            return respuestaJSON(
                {
                    ok: false,
                    error:
                        "Respuesta inválida de Gemini."
                },
                502,
                origen
            );
        }


        if (
            !respuestaGemini.ok
        ) {

            console.error(
                "Gemini:",
                datos
            );

            return respuestaJSON(
                {
                    ok: false,
                    error:
                        datos
                            ?.error
                            ?.message
                        ||
                        "Gemini rechazó la solicitud."
                },
                respuestaGemini.status,
                origen
            );
        }


        const texto =
            obtenerTextoGemini(
                datos
            );


        if (!texto) {

            return respuestaJSON(
                {
                    ok: false,
                    error:
                        "Gemini no devolvió texto."
                },
                502,
                origen
            );
        }


        return respuestaJSON(
            {
                ok: true,
                respuesta: texto,
                modelo:
                    MODELO_GEMINI,
                procedimientos_usados:
                    procedimientos.map(
                        p => p.id
                    )
            },
            200,
            origen
        );
    }
};