// ==========================================================
// SELECTOR DE CONSULTAS GENERALES
// NO MODIFICA EL MOTOR DE BÚSQUEDA
// NO MODIFICA LA BASE DE CONOCIMIENTO
// ==========================================================

(() => {

    "use strict";


    const RUTA_BASE =
        "data/base_conocimiento.json";


    let BASE_SELECTOR =
        null;


    // ======================================================
    // NORMALIZAR
    // ======================================================

    function normalizar(
        texto
    ) {

        return String(
            texto || ""
        )
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


    // ======================================================
    // CARGAR BASE
    // ======================================================

    async function cargarBase() {

        if (
            BASE_SELECTOR
        ) {

            return BASE_SELECTOR;
        }


        try {

            const respuesta =
                await fetch(
                    RUTA_BASE,
                    {
                        cache:
                            "no-store"
                    }
                );


            if (
                !respuesta.ok
            ) {

                throw new Error(
                    "No se pudo consultar la base."
                );
            }


            BASE_SELECTOR =
                await respuesta.json();


            return BASE_SELECTOR;


        } catch (
            error
        ) {

            console.warn(
                "Selector de consultas no disponible:",
                error
            );


            // IMPORTANTE:
            // si este módulo falla,
            // NO afecta al motor principal.

            return null;
        }
    }


    // ======================================================
    // DETECTAR VALIDACIÓN GENERAL
    // ======================================================

    function esIntencionValidacion(
        texto
    ) {

        return (
            /\bvalidacion\b/.test(texto)
            ||
            /\bvalidar\b/.test(texto)
            ||
            /\bvalido\b/.test(texto)
            ||
            /\bvalidando\b/.test(texto)
        );
    }


    // ======================================================
    // DETECTAR SI LA CONSULTA YA ES ESPECÍFICA
    // ======================================================

    function esConsultaEspecifica(
        texto
    ) {

        const terminosEspecificos = [

            "nivel",
            "niveles",
            "optico",
            "opticos",

            "receiving",
            "power",

            "firmware",

            "fat",
            "odn",
            "borne",
            "cintillo",

            "wan",
            "ip",

            "band steering",

            "iptv",

            "telefonia",
            "ocsi",

            "emta",
            "docsis",

            "repetidor",
            "mesh",

            "speedtest",
            "velocidad",

            "speech",

            "nps",

            "sga",

            "cierre"
        ];


        return terminosEspecificos.some(
            termino =>
                texto.includes(
                    termino
                )
        );
    }


    // ======================================================
    // FILTRO POR TIPO DE SOT
    // ======================================================

    function detectarTipo(
        texto
    ) {

        if (
            texto.includes(
                "instalacion"
            )
        ) {

            return "instalacion";
        }


        if (
            texto.includes(
                "mantenimiento"
            )
        ) {

            return "mantenimiento";
        }


        if (
            texto.includes(
                "migracion"
            )
        ) {

            return "migracion";
        }


        if (
            texto.includes(
                "postventa"
            )
        ) {

            return "postventa";
        }


        return null;
    }


    // ======================================================
    // TECNOLOGÍA
    // ======================================================

    function detectarTecnologia(
        texto
    ) {

        if (
            texto.includes(
                "ftth"
            )
            ||
            texto.includes(
                "fibra"
            )
        ) {

            return "ftth";
        }


        if (
            texto.includes(
                "hfc"
            )
        ) {

            return "hfc";
        }


        return null;
    }


    // ======================================================
    // BUSCAR OPCIONES
    // ======================================================

    async function buscarOpciones(
        pregunta
    ) {

        const texto =
            normalizar(
                pregunta
            );


        // --------------------------------------------------
        // No es una consulta sobre validación
        // --------------------------------------------------

        if (
            !esIntencionValidacion(
                texto
            )
        ) {

            return {
                ambigua:
                    false,

                opciones:
                    []
            };
        }


        // --------------------------------------------------
        // Ya indicó qué desea validar.
        // Dejamos trabajar al motor normal.
        // --------------------------------------------------

        if (
            esConsultaEspecifica(
                texto
            )
        ) {

            return {
                ambigua:
                    false,

                opciones:
                    []
            };
        }


        const base =
            await cargarBase();


        // Si este módulo falla, dejamos que el motor
        // principal continúe normalmente.

        if (
            !base
        ) {

            return {
                ambigua:
                    false,

                opciones:
                    []
            };
        }


        const tipo =
            detectarTipo(
                texto
            );


        const tecnologia =
            detectarTecnologia(
                texto
            );


        let procedimientos =
            (
                base.procedimientos ||
                []
            )
            .filter(
                procedimiento => {

                    if (
                        procedimiento
                            .control
                            ?.activo === false
                    ) {

                        return false;
                    }


                    return (
                        normalizar(
                            procedimiento.dominio
                        )
                        ===
                        "validacion"
                    );
                }
            );


        // --------------------------------------------------
        // FILTRAR POR TIPO
        // --------------------------------------------------

        if (
            tipo
        ) {

            procedimientos =
                procedimientos.filter(
                    procedimiento => {

                        const tipos =
                            (
                                procedimiento
                                    .clasificacion
                                    ?.tipo_sot ||
                                []
                            )
                            .map(
                                normalizar
                            );


                        return tipos.includes(
                            tipo
                        );
                    }
                );
        }


        // --------------------------------------------------
        // FILTRAR POR TECNOLOGÍA
        // --------------------------------------------------

        if (
            tecnologia
        ) {

            procedimientos =
                procedimientos.filter(
                    procedimiento => {

                        const tecnologias =
                            (
                                procedimiento
                                    .clasificacion
                                    ?.tecnologia ||
                                []
                            )
                            .map(
                                normalizar
                            );


                        return tecnologias.includes(
                            tecnologia
                        );
                    }
                );
        }


        // --------------------------------------------------
        // ORDENAR
        // --------------------------------------------------

        procedimientos.sort(
            (
                a,
                b
            ) => {

                return String(
                    a.id || ""
                )
                    .localeCompare(
                        String(
                            b.id || ""
                        ),
                        undefined,
                        {
                            numeric:
                                true
                        }
                    );
            }
        );


        const opciones =
            procedimientos.map(
                procedimiento => ({
                    id:
                        procedimiento.id,

                    titulo:
                        procedimiento.titulo,

                    resumen:
                        procedimiento
                            .respuesta
                            ?.resumen ||
                        ""
                })
            );


        // Solo intervenimos cuando realmente
        // hay varias posibilidades.

        if (
            opciones.length <= 1
        ) {

            return {
                ambigua:
                    false,

                opciones:
                    opciones
            };
        }


        return {

            ambigua:
                true,

            mensaje:
                (
                    "Encontré varios procedimientos relacionados " +
                    "con tu consulta. Selecciona qué deseas validar:"
                ),

            opciones:
                opciones
        };
    }


    // ======================================================
    // EXPONER
    // ======================================================

    window.SelectorConsultas = {

        buscarOpciones:
            buscarOpciones
    };


})();