// ==========================================================
// MOTOR DE BÚSQUEDA - ASISTENTE TÉCNICO
// ==========================================================

const RUTA_BASE_CONOCIMIENTO =
    "data/base_conocimiento.json";

const UMBRAL_RESPUESTA = 10;
const UMBRAL_ALTA = 20;
const UMBRAL_MEDIA = 14;
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


let BASE_CONOCIMIENTO = null;


// ==========================================================
// CARGAR BASE
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
                "No se pudo cargar base_conocimiento.json"
            );
        }

        BASE_CONOCIMIENTO =
            await respuesta.json();

        console.log(
            "Base cargada:",
            BASE_CONOCIMIENTO.metadata
        );

        console.log(
            "Procedimientos:",
            BASE_CONOCIMIENTO
                .procedimientos
                ?.length || 0
        );

        console.log(
            "Códigos:",
            BASE_CONOCIMIENTO
                .codigos_mantenimiento
                ?.length || 0
        );

        return BASE_CONOCIMIENTO;

    } catch (error) {

        console.error(
            "Error cargando la base:",
            error
        );

        BASE_CONOCIMIENTO = null;

        throw error;
    }
}


// ==========================================================
// NORMALIZAR
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

    const normalizado =
        normalizarTexto(texto);

    if (!normalizado) {
        return [];
    }

    return normalizado
        .split(" ")
        .filter(
            palabra =>
                palabra.length >= 3 &&
                !STOPWORDS.has(
                    palabra
                )
        );
}


// ==========================================================
// COMPARAR CONJUNTOS DE TOKENS
// ==========================================================

function mismosTokens(
    textoA,
    textoB
) {

    const tokensA =
        [...new Set(
            tokenizar(textoA)
        )].sort();

    const tokensB =
        [...new Set(
            tokenizar(textoB)
        )].sort();

    if (
        tokensA.length === 0 ||
        tokensB.length === 0
    ) {
        return false;
    }

    if (
        tokensA.length !==
        tokensB.length
    ) {
        return false;
    }

    return tokensA.every(
        (
            token,
            indice
        ) =>
            token ===
            tokensB[indice]
    );
}


// ==========================================================
// TOKENS COMUNES
// ==========================================================

function contarTokensComunes(
    textoA,
    textoB
) {

    const tokensA =
        new Set(
            tokenizar(textoA)
        );

    const tokensB =
        new Set(
            tokenizar(textoB)
        );

    let cantidad = 0;

    for (
        const token
        of tokensA
    ) {

        if (
            tokensB.has(token)
        ) {

            cantidad++;
        }
    }

    return cantidad;
}


// ==========================================================
// SIMILITUD LEVENSHTEIN
// ==========================================================

function similitudTexto(
    textoA,
    textoB
) {

    const a =
        normalizarTexto(
            textoA
        );

    const b =
        normalizarTexto(
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
                b[i - 1] ===
                a[j - 1]
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
        matriz[
            b.length
        ][
            a.length
        ];

    const longitud =
        Math.max(
            a.length,
            b.length
        );

    return (
        1 -
        distancia /
        longitud
    );
}


// ==========================================================
// EXTRAER CÓDIGOS
// ==========================================================

function extraerCodigos(texto) {

    const coincidencias =
        String(
            texto || ""
        ).match(
            /\b[A-Za-z]{2}\d{2}\b/g
        );

    if (!coincidencias) {
        return [];
    }

    return coincidencias.map(
        codigo =>
            codigo.toUpperCase()
    );
}


// ==========================================================
// BUSCAR CÓDIGO
// ==========================================================

function buscarCodigoMantenimiento(
    pregunta,
    base
) {

    const codigos =
        extraerCodigos(
            pregunta
        );

    if (
        codigos.length === 0
    ) {

        return null;
    }

    const catalogo =
        base.codigos_mantenimiento ||
        [];

    for (
        const codigoPregunta
        of codigos
    ) {

        for (
            const registro
            of catalogo
        ) {

            if (
                registro
                    .control
                    ?.activo
                === false
            ) {

                continue;
            }

            const codigoBase =
                String(
                    registro.codigo ||
                    ""
                )
                    .trim()
                    .toUpperCase();

            if (
                codigoBase ===
                codigoPregunta
            ) {

                return registro;
            }
        }
    }

    return null;
}


// ==========================================================
// RESPUESTA CÓDIGO
// ==========================================================

function construirRespuestaCodigo(
    registro
) {

    const lineas = [
        "CÓDIGO DE MANTENIMIENTO",
        "",
        `Código: ${registro.codigo || ""}`,
        `Categoría: ${registro.categoria || ""}`,
        `Significado: ${registro.significado || ""}`
    ];

    if (
        registro.detalle_adicional
    ) {

        lineas.push(
            `Detalle adicional: ${registro.detalle_adicional}`
        );
    }

    if (
        registro.registro_sga
    ) {

        lineas.push("");
        lineas.push(
            `Registro SGA: ${registro.registro_sga}`
        );
    }

    return lineas.join(
        "\n"
    );
}


// ==========================================================
// TEXTOS DEL PROCEDIMIENTO
// ==========================================================

function obtenerTextosBusqueda(
    procedimiento
) {

    const textos = [];

    textos.push({
        campo:
            "titulo",

        texto:
            procedimiento
                .titulo || "",

        peso:
            9
    });

    const busqueda =
        procedimiento.busqueda ||
        {};

    for (
        const consulta
        of (
            busqueda
                .consultas_ejemplo ||
            []
        )
    ) {

        textos.push({
            campo:
                "consulta_ejemplo",

            texto:
                consulta,

            peso:
                12
        });
    }

    for (
        const palabra
        of (
            busqueda
                .palabras_clave ||
            []
        )
    ) {

        textos.push({
            campo:
                "palabra_clave",

            texto:
                palabra,

            peso:
                3
        });
    }

    for (
        const sinonimo
        of (
            busqueda.sinonimos ||
            []
        )
    ) {

        textos.push({
            campo:
                "sinonimo",

            texto:
                sinonimo,

            peso:
                5
        });
    }

    const clasificacion =
        procedimiento
            .clasificacion ||
        {};

    for (
        const tipo
        of (
            clasificacion
                .tipo_sot ||
            []
        )
    ) {

        textos.push({
            campo:
                "tipo_sot",

            texto:
                tipo,

            peso:
                2
        });
    }

    for (
        const tecnologia
        of (
            clasificacion
                .tecnologia ||
            []
        )
    ) {

        textos.push({
            campo:
                "tecnologia",

            texto:
                tecnologia,

            peso:
                3
        });
    }

    for (
        const aplicativo
        of (
            clasificacion
                .aplicativos ||
            []
        )
    ) {

        textos.push({
            campo:
                "aplicativo",

            texto:
                aplicativo,

            peso:
                2
        });
    }

    return textos;
}


// ==========================================================
// VALIDAR EVIDENCIA
// ==========================================================

function evaluarEvidenciaLexica(
    pregunta,
    procedimiento
) {

    const tokensPregunta =
        tokenizar(
            pregunta
        );

    if (
        tokensPregunta.length < 2
    ) {

        return false;
    }

    const textos =
        obtenerTextosBusqueda(
            procedimiento
        );

    let maxComunes = 0;

    for (
        const item
        of textos
    ) {

        const comunes =
            contarTokensComunes(
                pregunta,
                item.texto
            );

        maxComunes =
            Math.max(
                maxComunes,
                comunes
            );

        if (
            (
                item.campo ===
                "consulta_ejemplo"
                ||
                item.campo ===
                "titulo"
                ||
                item.campo ===
                "sinonimo"
            )
            &&
            mismosTokens(
                pregunta,
                item.texto
            )
        ) {

            return true;
        }
    }

    return (
        maxComunes >= 2
    );
}


// ==========================================================
// PUNTUAR PROCEDIMIENTO
// ==========================================================

function puntuarProcedimiento(
    pregunta,
    procedimiento
) {

    if (
        !evaluarEvidenciaLexica(
            pregunta,
            procedimiento
        )
    ) {

        return {
            puntuacion: 0,
            razones: []
        };
    }

    const preguntaN =
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

        const textoN =
            normalizarTexto(
                item.texto
            );

        if (!textoN) {
            continue;
        }

        const tokensTexto =
            tokenizar(
                item.texto
            );

        const comunes =
            contarTokensComunes(
                pregunta,
                item.texto
            );

        let puntos = 0;


        // ==================================================
        // CONSULTA EJEMPLO CASI EXACTA
        // ==================================================

        if (
            item.campo ===
            "consulta_ejemplo"
            &&
            mismosTokens(
                pregunta,
                item.texto
            )
        ) {

            puntos += 25;
        }


        // ==================================================
        // TÍTULO CASI EXACTO
        // ==================================================

        else if (
            item.campo ===
            "titulo"
            &&
            mismosTokens(
                pregunta,
                item.texto
            )
        ) {

            puntos += 20;
        }


        // ==================================================
        // COINCIDENCIA EXACTA
        // ==================================================

        else if (
            textoN ===
            preguntaN
        ) {

            puntos +=
                item.peso +
                10;
        }


        // ==================================================
        // FRASES DE DOS O MÁS PALABRAS
        // ==================================================

        else if (
            tokensTexto.length >= 2
        ) {

            if (
                preguntaN.includes(
                    textoN
                )
            ) {

                puntos +=
                    item.peso +
                    4;

            } else if (
                textoN.includes(
                    preguntaN
                )
            ) {

                puntos +=
                    item.peso *
                    0.7;
            }
        }


        // ==================================================
        // TOKENS COMUNES
        // ==================================================

        if (
            comunes > 0
        ) {

            const cobertura =
                comunes /
                Math.max(
                    tokensPregunta.length,
                    1
                );

            puntos +=
                cobertura *
                item.peso;

            if (
                comunes >= 2
            ) {

                puntos +=
                    Math.min(
                        3,
                        comunes * 0.7
                    );
            }
        }


        // ==================================================
        // SIMILITUD
        // Solo apoyo, nunca criterio principal
        // ==================================================

        if (
            comunes >= 1 &&
            tokensTexto.length >= 2
        ) {

            const similitud =
                similitudTexto(
                    pregunta,
                    item.texto
                );

            if (
                similitud >= 0.60
            ) {

                puntos +=
                    similitud *
                    item.peso *
                    0.25;
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
                        puntos.toFixed(
                            2
                        )
                    )
            });
        }
    }


    // ======================================================
    // BONUS POR DOMINIO EXPLÍCITO
    // ======================================================

    const preguntaNormalizada =
        normalizarTexto(
            pregunta
        );

    const dominio =
        normalizarTexto(
            procedimiento
                .dominio ||
            ""
        );

    if (
        dominio ===
        "validacion"
        &&
        (
            preguntaNormalizada
                .includes(
                    "valido"
                )
            ||
            preguntaNormalizada
                .includes(
                    "validar"
                )
            ||
            preguntaNormalizada
                .includes(
                    "validacion"
                )
        )
    ) {

        puntuacion += 4;

        razones.push({
            campo:
                "intencion_dominio",

            valor:
                "validacion",

            puntos:
                4
        });
    }


    return {
        puntuacion:
            Number(
                puntuacion.toFixed(
                    2
                )
            ),

        razones:
            razones
    };
}


// ==========================================================
// BUSCAR PROCEDIMIENTOS
// ==========================================================

function buscarProcedimientos(
    pregunta,
    base
) {

    const resultados = [];

    for (
        const procedimiento
        of (
            base.procedimientos ||
            []
        )
    ) {

        if (
            procedimiento
                .control
                ?.activo
            === false
        ) {

            continue;
        }

        const evaluacion =
            puntuarProcedimiento(
                pregunta,
                procedimiento
            );

        if (
            evaluacion.puntuacion <
            UMBRAL_RESPUESTA
        ) {

            continue;
        }

        let confianza =
            "BAJA";

        if (
            evaluacion.puntuacion >=
            UMBRAL_ALTA
        ) {

            confianza =
                "ALTA";

        } else if (
            evaluacion.puntuacion >=
            UMBRAL_MEDIA
        ) {

            confianza =
                "MEDIA";
        }

        resultados.push({
            procedimiento:
                procedimiento,

            puntuacion:
                evaluacion
                    .puntuacion,

            confianza:
                confianza,

            razones:
                evaluacion
                    .razones
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
// CONSTRUIR RESPUESTA PROCEDIMIENTO
// ==========================================================

function construirRespuestaProcedimiento(
    procedimiento
) {

    const respuesta =
        procedimiento.respuesta ||
        {};

    const lineas = [
        `PROCEDIMIENTO: ${procedimiento.titulo || ""}`
    ];


    if (
        respuesta.resumen
    ) {

        lineas.push("");
        lineas.push(
            respuesta.resumen
        );
    }


    const pasos =
        respuesta.pasos ||
        [];

    if (
        pasos.length > 0
    ) {

        lineas.push("");
        lineas.push(
            "PASOS:"
        );

        const ordenados =
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
            of ordenados
        ) {

            let texto =
                `${paso.orden || ""}. `;

            if (
                paso.aplicativo
            ) {

                texto +=
                    `[${paso.aplicativo}] `;
            }

            texto +=
                paso.accion ||
                "";

            lineas.push(
                texto
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


    const secciones = [
        [
            "PRECONDICIONES",
            "precondiciones"
        ],
        [
            "VERIFICAR",
            "verificaciones"
        ],
        [
            "ADVERTENCIAS",
            "advertencias"
        ]
    ];


    for (
        const [
            titulo,
            campo
        ]
        of secciones
    ) {

        const elementos =
            respuesta[campo] ||
            [];

        if (
            elementos.length > 0
        ) {

            lineas.push("");
            lineas.push(
                `${titulo}:`
            );

            for (
                const elemento
                of elementos
            ) {

                lineas.push(
                    `- ${elemento}`
                );
            }
        }
    }


    if (
        respuesta
            .accion_si_no_cumple
    ) {

        lineas.push("");
        lineas.push(
            "SI NO CUMPLE:"
        );

        lineas.push(
            respuesta
                .accion_si_no_cumple
        );
    }


    if (
        respuesta.escalamiento
    ) {

        lineas.push("");
        lineas.push(
            "ESCALAMIENTO:"
        );

        lineas.push(
            respuesta.escalamiento
        );
    }


    return lineas.join(
        "\n"
    );
}


// ==========================================================
// CONSULTAR
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
                "La base de conocimiento no está cargada.",

            resultados:
                []
        };
    }


    const respuestaSinResultado =
        BASE_CONOCIMIENTO
            .configuracion
            ?.respuesta_sin_resultado
        ||
        (
            "No existe información confirmada " +
            "para esta consulta en la base de conocimiento. " +
            "Consulta con tu supervisor a cargo."
        );


    const texto =
        String(
            pregunta ||
            ""
        ).trim();


    if (!texto) {

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
    // CÓDIGOS
    // ======================================================

    const codigo =
        buscarCodigoMantenimiento(
            texto,
            BASE_CONOCIMIENTO
        );


    if (codigo) {

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


    const codigosEscritos =
        extraerCodigos(
            texto
        );


    if (
        codigosEscritos.length >
        0
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
    // CONSULTAS CORTAS
    // ======================================================

    if (
        tokenizar(
            texto
        ).length < 2
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
    // PROCEDIMIENTOS
    // ======================================================

    const resultados =
        buscarProcedimientos(
            texto,
            BASE_CONOCIMIENTO
        );


    if (
        resultados.length ===
        0
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
// DIAGNÓSTICO
// ==========================================================

function diagnosticar(
    pregunta
) {

    if (
        !BASE_CONOCIMIENTO
    ) {

        console.log(
            "La base aún no está cargada."
        );

        return [];
    }


    const resultados =
        buscarProcedimientos(
            pregunta,
            BASE_CONOCIMIENTO
        );


    console.table(
        resultados.map(
            resultado => ({
                id:
                    resultado
                        .procedimiento
                        .id,

                titulo:
                    resultado
                        .procedimiento
                        .titulo,

                puntuacion:
                    resultado
                        .puntuacion,

                confianza:
                    resultado
                        .confianza
            })
        )
    );


    return resultados;
}


// ==========================================================
// INICIALIZAR
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
                "No se pudo cargar la base.",
            error:
                error
        };
    }
}


// ==========================================================
// EXPONER AL HTML
// ==========================================================

window.AsistenteMotor = {

    inicializar:
        inicializarMotor,

    consultar:
        consultar,

    diagnosticar:
        diagnosticar,

    cargarBaseConocimiento:
        cargarBaseConocimiento,

    normalizarTexto:
        normalizarTexto,

    tokenizar:
        tokenizar,

    extraerCodigos:
        extraerCodigos
};