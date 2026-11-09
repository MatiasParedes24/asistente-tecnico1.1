// ==========================================================
// IA GEMINI - ASISTENTE OPERATIVO
//
// NUEVO FLUJO:
//
// Pregunta natural
//      ↓
// Cloudflare Worker
//      ↓
// Gemini busca semánticamente en la base
//      ↓
// Worker verifica las referencias
//      ↓
// Gemini responde SOLO con información autorizada
//
// El motor local queda como respaldo.
// ==========================================================

(() => {

    "use strict";


    // ======================================================
    // CONFIGURACIÓN
    // ======================================================

    const URL_BACKEND_GEMINI =
        "https://asistente-tecnico-gemini.asistente-operativo.workers.dev/consultar";


    // ======================================================
    // ENVIAR SOLICITUD AL BACKEND
    // ======================================================

    async function enviarSolicitud(
        datosEnvio
    ) {

        try {

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
                                datosEnvio
                            )
                    }
                );


            // =================================================
            // LEER RESPUESTA
            // =================================================

            let datos;


            try {

                datos =
                    await respuesta.json();

            } catch (
                error
            ) {

                console.error(
                    "Respuesta no JSON:",
                    error
                );


                return {

                    ok:
                        false,

                    tipo:
                        "error",

                    error:
                        "El backend devolvió una respuesta inválida."
                };
            }


            // =================================================
            // ERROR HTTP
            // =================================================

            if (
                !respuesta.ok
            ) {

                console.error(
                    "Error backend Gemini:",
                    datos
                );


                return {

                    ok:
                        false,

                    tipo:
                        datos.tipo ||
                        "error",

                    error:
                        datos.error ||
                        "No fue posible utilizar el servicio de IA."
                };
            }


            // =================================================
            // RESPUESTA CORRECTA
            // =================================================

            return {

                ok:
                    datos.ok === true,

                tipo:
                    datos.tipo ||
                    "respuesta",

                respuesta:
                    datos.respuesta ||
                    "",

                opciones:
                    Array.isArray(
                        datos.opciones
                    )
                        ?
                        datos.opciones
                        :
                        [],

                modelo:
                    datos.modelo ||
                    "",

                fuentes_usadas:
                    Array.isArray(
                        datos.fuentes_usadas
                    )
                        ?
                        datos.fuentes_usadas
                        :
                        [],

                procedimientos_usados:
                    Array.isArray(
                        datos.procedimientos_usados
                    )
                        ?
                        datos.procedimientos_usados
                        :
                        [],

                codigos_usados:
                    Array.isArray(
                        datos.codigos_usados
                    )
                        ?
                        datos.codigos_usados
                        :
                        []
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

                tipo:
                    "error",

                error:
                    "No se pudo establecer conexión con el servicio de IA."
            };
        }
    }


    // ======================================================
    // CONSULTA SEMÁNTICA NORMAL
    //
    // El navegador NO decide qué procedimiento usar.
    // El Worker + Gemini realizan la recuperación semántica.
    // ======================================================

    async function consultarSemantico(
        pregunta
    ) {

        const texto =
            String(
                pregunta ||
                ""
            )
            .trim();


        if (
            !texto
        ) {

            return {

                ok:
                    false,

                tipo:
                    "error",

                error:
                    "La consulta está vacía."
            };
        }


        return await enviarSolicitud(
            {

                pregunta:
                    texto
            }
        );
    }


    // ======================================================
    // CONSULTAR CON REFERENCIAS SELECCIONADAS
    //
    // Se utiliza cuando Gemini detecta una pregunta ambigua
    // y el usuario selecciona una tarjeta.
    //
    // Ejemplo:
    //
    // refs = ["P:VAL002"]
    // ======================================================

    async function consultarConReferencias(
        pregunta,
        referencias
    ) {

        const texto =
            String(
                pregunta ||
                ""
            )
            .trim();


        const refs =
            Array.isArray(
                referencias
            )
                ?
                referencias
                    .map(
                        referencia =>
                            String(
                                referencia ||
                                ""
                            )
                            .trim()
                            .toUpperCase()
                    )
                    .filter(
                        Boolean
                    )
                :
                [];


        if (
            !texto
        ) {

            return {

                ok:
                    false,

                tipo:
                    "error",

                error:
                    "La consulta está vacía."
            };
        }


        if (
            refs.length ===
            0
        ) {

            return {

                ok:
                    false,

                tipo:
                    "error",

                error:
                    "No se seleccionó una referencia válida."
            };
        }


        return await enviarSolicitud(
            {

                pregunta:
                    texto,

                refs:
                    refs
            }
        );
    }


    // ======================================================
    // EXTRAER REFERENCIAS DESDE RESULTADOS DEL MOTOR LOCAL
    //
    // Se conserva únicamente por compatibilidad y respaldo.
    // ======================================================

    function obtenerReferenciasLocales(
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

            .map(
                resultado => {

                    const id =
                        resultado
                            ?.procedimiento
                            ?.id;


                    if (
                        !id
                    ) {

                        return "";
                    }


                    return (
                        "P:" +
                        String(
                            id
                        )
                        .trim()
                        .toUpperCase()
                    );
                }
            )

            .filter(
                Boolean
            )

            .slice(
                0,
                5
            );
    }


    // ======================================================
    // CONSULTAR UTILIZANDO RESULTADOS LOCALES
    //
    // Solo se usa como compatibilidad con código anterior.
    // ======================================================

    async function consultarConResultadosLocales(
        pregunta,
        resultadosMotor
    ) {

        const refs =
            obtenerReferenciasLocales(
                resultadosMotor
            );


        if (
            refs.length ===
            0
        ) {

            return await consultarSemantico(
                pregunta
            );
        }


        return await consultarConReferencias(
            pregunta,
            refs
        );
    }


    // ======================================================
    // COMPATIBILIDAD
    //
    // Permite que código anterior todavía pueda ejecutar:
    //
    // AsistenteIA.consultar(pregunta, resultadosMotor)
    //
    // Pero el nuevo frontend utilizará:
    //
    // AsistenteIA.consultar(pregunta)
    // ======================================================

    async function consultar(
        pregunta,
        resultadosMotor = null
    ) {

        if (
            Array.isArray(
                resultadosMotor
            )
            &&
            resultadosMotor.length >
            0
        ) {

            return await consultarConResultadosLocales(
                pregunta,
                resultadosMotor
            );
        }


        return await consultarSemantico(
            pregunta
        );
    }


    // ======================================================
    // COMPATIBILIDAD CON FUNCIÓN ANTIGUA
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

            .map(
                resultado =>
                    resultado
                        ?.procedimiento
                        ?.id ||
                    ""
            )

            .filter(
                Boolean
            )

            .slice(
                0,
                5
            );
    }


    // ======================================================
    // EXPONER API
    // ======================================================

    window.AsistenteIA = {

        consultar:
            consultar,

        consultarSemantico:
            consultarSemantico,

        consultarConReferencias:
            consultarConReferencias,

        consultarConResultadosLocales:
            consultarConResultadosLocales,

        obtenerReferenciasLocales:
            obtenerReferenciasLocales,

        obtenerIdsProcedimientos:
            obtenerIdsProcedimientos
    };


})();