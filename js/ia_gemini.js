// ==========================================================
// IA GEMINI - ASISTENTE TÉCNICO
// ==========================================================

(() => {

    "use strict";


    // ======================================================
    // CONFIGURACIÓN
    // ======================================================

    const URL_BACKEND_GEMINI =
        "https://asistente-tecnico-gemini.asistente-operativo.workers.dev/consultar";


    // ======================================================
    // OBTENER IDS DE LOS PROCEDIMIENTOS
    // ======================================================

    function obtenerIdsProcedimientos(
        resultadosMotor
    ) {

        if (
            !Array.isArray(
                resultadosMotor
            )
        ) {

            return [];
        }


        return resultadosMotor
            .slice(
                0,
                3
            )
            .map(
                resultado =>
                    resultado
                        ?.procedimiento
                        ?.id || ""
            )
            .filter(
                id => id
            );
    }


    // ======================================================
    // CONSULTAR GEMINI
    // ======================================================

    async function consultarGemini(
        pregunta,
        resultadosMotor
    ) {

        const ids =
            obtenerIdsProcedimientos(
                resultadosMotor
            );


        // --------------------------------------------------
        // Sin procedimientos autorizados
        // --------------------------------------------------

        if (
            ids.length ===
            0
        ) {

            return {

                ok:
                    false,

                error:
                    "No existen procedimientos autorizados para enviar a la IA."
            };
        }


        try {

            // --------------------------------------------------
            // CONSULTAR CLOUDFLARE WORKER
            // --------------------------------------------------

            const respuesta =
                await fetch(
                    URL_BACKEND_GEMINI,
                    {
                        method:
                            "POST",

                        headers: {

                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify(
                                {

                                    pregunta:
                                        pregunta,

                                    ids:
                                        ids
                                }
                            )
                    }
                );


            // --------------------------------------------------
            // LEER RESPUESTA
            // --------------------------------------------------

            let datos;


            try {

                datos =
                    await respuesta.json();

            } catch {

                return {

                    ok:
                        false,

                    error:
                        "El backend devolvió una respuesta inválida."
                };
            }


            // --------------------------------------------------
            // ERROR DEL BACKEND
            // --------------------------------------------------

            if (
                !respuesta.ok
            ) {

                console.error(
                    "Error del backend Gemini:",
                    datos
                );


                return {

                    ok:
                        false,

                    error:
                        datos.error ||
                        "No fue posible utilizar Gemini."
                };
            }


            // --------------------------------------------------
            // SIN RESPUESTA
            // --------------------------------------------------

            if (
                !datos.respuesta
            ) {

                return {

                    ok:
                        false,

                    error:
                        "Gemini no devolvió una respuesta."
                };
            }


            // --------------------------------------------------
            // RESPUESTA CORRECTA
            // --------------------------------------------------

            return {

                ok:
                    true,

                respuesta:
                    datos.respuesta,

                modelo:
                    datos.modelo ||
                    "",

                procedimientos_usados:
                    datos.procedimientos_usados ||
                    ids
            };


        } catch (
            error
        ) {

            console.error(
                "Error conectando con Gemini:",
                error
            );


            return {

                ok:
                    false,

                error:
                    "No se pudo establecer conexión con el servicio de IA."
            };
        }
    }


    // ======================================================
    // EXPONER ÚNICAMENTE EL MÓDULO
    // ======================================================

    window.AsistenteIA = {

        consultar:
            consultarGemini,

        obtenerIdsProcedimientos:
            obtenerIdsProcedimientos
    };


})();