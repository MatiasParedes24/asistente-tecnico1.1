import json
import re
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher


# ==========================================================
# RUTAS
# ==========================================================

RAIZ = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

ARCHIVO_BD = (
    RAIZ
    / "data"
    / "base_conocimiento.json"
)


# ==========================================================
# CONFIGURACIÓN DEL MOTOR
# ==========================================================

PESO_TITULO = 6.0
PESO_CONSULTA_EJEMPLO = 5.0
PESO_PALABRA_CLAVE = 4.0
PESO_SINONIMO = 4.0
PESO_APLICATIVO = 2.5
PESO_TIPO_SOT = 2.5
PESO_TECNOLOGIA = 2.5
PESO_DOMINIO = 2.0

BONUS_FRASE_COMPLETA = 4.0
BONUS_MULTIPLES_COINCIDENCIAS = 2.0

UMBRAL_MINIMO = 3.0

MAX_RESULTADOS = 5


# ==========================================================
# PALABRAS QUE APORTAN POCO SIGNIFICADO
# ==========================================================

STOPWORDS = {
    "a",
    "al",
    "algo",
    "como",
    "con",
    "cual",
    "cuales",
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
    "y"
}


# ==========================================================
# CARGA DE BASE
# ==========================================================

def cargar_base():

    if not ARCHIVO_BD.exists():

        raise FileNotFoundError(
            "No se encontró "
            "data/base_conocimiento.json"
        )

    with open(
        ARCHIVO_BD,
        "r",
        encoding="utf-8"
    ) as archivo:

        return json.load(archivo)


# ==========================================================
# NORMALIZACIÓN DE TEXTO
# ==========================================================

def normalizar_texto(texto):

    if texto is None:
        return ""

    texto = str(texto).lower()

    texto = "".join(
        caracter
        for caracter in unicodedata.normalize(
            "NFD",
            texto
        )
        if unicodedata.category(
            caracter
        ) != "Mn"
    )

    texto = re.sub(
        r"[^a-z0-9\s]",
        " ",
        texto
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


def tokenizar(texto):

    texto = normalizar_texto(
        texto
    )

    palabras = texto.split()

    return [
        palabra
        for palabra in palabras
        if palabra not in STOPWORDS
        and len(palabra) > 1
    ]


# ==========================================================
# SIMILITUD DE TEXTO
# ==========================================================

def similitud_textual(
    texto_a,
    texto_b
):

    a = normalizar_texto(
        texto_a
    )

    b = normalizar_texto(
        texto_b
    )

    if not a or not b:
        return 0.0

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio()


def coincidencia_tokens(
    pregunta,
    texto
):

    tokens_pregunta = set(
        tokenizar(
            pregunta
        )
    )

    tokens_texto = set(
        tokenizar(
            texto
        )
    )

    if not tokens_pregunta:
        return 0.0

    comunes = (
        tokens_pregunta
        & tokens_texto
    )

    return (
        len(comunes)
        /
        len(tokens_pregunta)
    )


# ==========================================================
# EVALUACIÓN DE FRASES
# ==========================================================

def puntuar_texto(
    pregunta,
    texto,
    peso
):

    if not texto:
        return 0.0

    pregunta_normalizada = (
        normalizar_texto(
            pregunta
        )
    )

    texto_normalizado = (
        normalizar_texto(
            texto
        )
    )

    puntuacion = 0.0

    # ------------------------------------------------------
    # FRASE COMPLETA
    # ------------------------------------------------------

    if (
        texto_normalizado
        in pregunta_normalizada
    ):

        puntuacion += (
            peso
            + BONUS_FRASE_COMPLETA
        )

    # ------------------------------------------------------
    # PALABRAS COINCIDENTES
    # ------------------------------------------------------

    porcentaje_tokens = (
        coincidencia_tokens(
            pregunta,
            texto
        )
    )

    puntuacion += (
        porcentaje_tokens
        * peso
    )

    # ------------------------------------------------------
    # SIMILITUD GENERAL
    # ------------------------------------------------------

    similitud = (
        similitud_textual(
            pregunta,
            texto
        )
    )

    if similitud >= 0.50:

        puntuacion += (
            similitud
            * peso
            * 0.7
        )

    return puntuacion


# ==========================================================
# PUNTUAR PROCEDIMIENTO
# ==========================================================

def puntuar_procedimiento(
    pregunta,
    procedimiento
):

    puntuacion = 0.0

    razones = []

    # ------------------------------------------------------
    # TÍTULO
    # ------------------------------------------------------

    titulo = procedimiento.get(
        "titulo",
        ""
    )

    puntos = puntuar_texto(
        pregunta,
        titulo,
        PESO_TITULO
    )

    if puntos > 0:

        puntuacion += puntos

        razones.append(
            (
                "titulo",
                titulo,
                round(
                    puntos,
                    2
                )
            )
        )

    # ------------------------------------------------------
    # DOMINIO
    # ------------------------------------------------------

    dominio = procedimiento.get(
        "dominio",
        ""
    )

    puntos = puntuar_texto(
        pregunta,
        dominio,
        PESO_DOMINIO
    )

    if puntos > 0:

        puntuacion += puntos

        razones.append(
            (
                "dominio",
                dominio,
                round(
                    puntos,
                    2
                )
            )
        )

    # ------------------------------------------------------
    # BÚSQUEDA
    # ------------------------------------------------------

    busqueda = procedimiento.get(
        "busqueda",
        {}
    )

    for consulta in busqueda.get(
        "consultas_ejemplo",
        []
    ):

        puntos = puntuar_texto(
            pregunta,
            consulta,
            PESO_CONSULTA_EJEMPLO
        )

        if puntos > 0:

            puntuacion += puntos

            razones.append(
                (
                    "consulta",
                    consulta,
                    round(
                        puntos,
                        2
                    )
                )
            )

    for palabra in busqueda.get(
        "palabras_clave",
        []
    ):

        puntos = puntuar_texto(
            pregunta,
            palabra,
            PESO_PALABRA_CLAVE
        )

        if puntos > 0:

            puntuacion += puntos

            razones.append(
                (
                    "palabra_clave",
                    palabra,
                    round(
                        puntos,
                        2
                    )
                )
            )

    for sinonimo in busqueda.get(
        "sinonimos",
        []
    ):

        puntos = puntuar_texto(
            pregunta,
            sinonimo,
            PESO_SINONIMO
        )

        if puntos > 0:

            puntuacion += puntos

            razones.append(
                (
                    "sinonimo",
                    sinonimo,
                    round(
                        puntos,
                        2
                    )
                )
            )

    # ------------------------------------------------------
    # CLASIFICACIÓN
    # ------------------------------------------------------

    clasificacion = procedimiento.get(
        "clasificacion",
        {}
    )

    for tipo_sot in clasificacion.get(
        "tipo_sot",
        []
    ):

        puntos = puntuar_texto(
            pregunta,
            tipo_sot,
            PESO_TIPO_SOT
        )

        if puntos > 0:

            puntuacion += puntos

            razones.append(
                (
                    "tipo_sot",
                    tipo_sot,
                    round(
                        puntos,
                        2
                    )
                )
            )

    for tecnologia in clasificacion.get(
        "tecnologia",
        []
    ):

        puntos = puntuar_texto(
            pregunta,
            tecnologia,
            PESO_TECNOLOGIA
        )

        if puntos > 0:

            puntuacion += puntos

            razones.append(
                (
                    "tecnologia",
                    tecnologia,
                    round(
                        puntos,
                        2
                    )
                )
            )

    for aplicativo in clasificacion.get(
        "aplicativos",
        []
    ):

        puntos = puntuar_texto(
            pregunta,
            aplicativo,
            PESO_APLICATIVO
        )

        if puntos > 0:

            puntuacion += puntos

            razones.append(
                (
                    "aplicativo",
                    aplicativo,
                    round(
                        puntos,
                        2
                    )
                )
            )

    # ------------------------------------------------------
    # BONUS POR MÚLTIPLES INDICIOS
    # ------------------------------------------------------

    if len(razones) >= 3:

        puntuacion += (
            BONUS_MULTIPLES_COINCIDENCIAS
        )

    return (
        puntuacion,
        razones
    )


# ==========================================================
# BUSCAR PROCEDIMIENTOS
# ==========================================================

def buscar_procedimientos(
    pregunta,
    base,
    solo_activos=True,
    solo_validados=False
):

    resultados = []

    for procedimiento in base.get(
        "procedimientos",
        []
    ):

        control = procedimiento.get(
            "control",
            {}
        )

        if (
            solo_activos
            and not control.get(
                "activo",
                True
            )
        ):

            continue

        if (
            solo_validados
            and not control.get(
                "validado",
                False
            )
        ):

            continue

        puntuacion, razones = (
            puntuar_procedimiento(
                pregunta,
                procedimiento
            )
        )

        if puntuacion >= UMBRAL_MINIMO:

            resultados.append(
                {
                    "procedimiento":
                        procedimiento,

                    "puntuacion":
                        round(
                            puntuacion,
                            2
                        ),

                    "razones":
                        razones
                }
            )

    resultados.sort(
        key=lambda item: (
            item[
                "puntuacion"
            ]
        ),
        reverse=True
    )

    return resultados[
        :MAX_RESULTADOS
    ]


# ==========================================================
# CÓDIGOS DE MANTENIMIENTO
# ==========================================================

def buscar_codigo_mantenimiento(
    pregunta,
    base
):

    pregunta_normalizada = (
        normalizar_texto(
            pregunta
        )
    )

    resultados = []

    for registro in base.get(
        "codigos_mantenimiento",
        []
    ):

        control = registro.get(
            "control",
            {}
        )

        if not control.get(
            "activo",
            True
        ):

            continue

        codigo = registro.get(
            "codigo",
            ""
        )

        codigo_normalizado = (
            normalizar_texto(
                codigo
            )
        )

        if (
            codigo_normalizado
            and codigo_normalizado
            in pregunta_normalizada
        ):

            resultados.append(
                registro
            )

    return resultados


# ==========================================================
# FORMATEAR RESPUESTA
# ==========================================================

def construir_respuesta(
    procedimiento
):

    respuesta = procedimiento.get(
        "respuesta",
        {}
    )

    lineas = []

    lineas.append(
        f"PROCEDIMIENTO: "
        f"{procedimiento.get('titulo', '')}"
    )

    lineas.append("")

    resumen = respuesta.get(
        "resumen",
        ""
    )

    if resumen:

        lineas.append(
            resumen
        )

    pasos = respuesta.get(
        "pasos",
        []
    )

    if pasos:

        lineas.append("")
        lineas.append(
            "PASOS:"
        )

        for paso in sorted(
            pasos,
            key=lambda x: x.get(
                "orden",
                0
            )
        ):

            numero = paso.get(
                "orden",
                ""
            )

            aplicativo = paso.get(
                "aplicativo",
                ""
            )

            accion = paso.get(
                "accion",
                ""
            )

            if aplicativo:

                texto_paso = (
                    f"{numero}. "
                    f"[{aplicativo}] "
                    f"{accion}"
                )

            else:

                texto_paso = (
                    f"{numero}. "
                    f"{accion}"
                )

            lineas.append(
                texto_paso
            )

            validacion = paso.get(
                "validacion",
                ""
            )

            if validacion:

                lineas.append(
                    "   Verificar: "
                    + validacion
                )

            no_cumple = paso.get(
                "si_no_cumple",
                ""
            )

            if no_cumple:

                lineas.append(
                    "   Si no cumple: "
                    + no_cumple
                )

    precondiciones = respuesta.get(
        "precondiciones",
        []
    )

    if precondiciones:

        lineas.append("")
        lineas.append(
            "ANTES DE CONTINUAR:"
        )

        for item in precondiciones:

            lineas.append(
                f"- {item}"
            )

    verificaciones = respuesta.get(
        "verificaciones",
        []
    )

    if verificaciones:

        lineas.append("")
        lineas.append(
            "VERIFICAR:"
        )

        for item in verificaciones:

            lineas.append(
                f"- {item}"
            )

    advertencias = respuesta.get(
        "advertencias",
        []
    )

    if advertencias:

        lineas.append("")
        lineas.append(
            "ADVERTENCIAS:"
        )

        for item in advertencias:

            lineas.append(
                f"- {item}"
            )

    accion_no_cumple = (
        respuesta.get(
            "accion_si_no_cumple",
            ""
        )
    )

    if accion_no_cumple:

        lineas.append("")
        lineas.append(
            "SI NO CUMPLE:"
        )

        lineas.append(
            accion_no_cumple
        )

    escalamiento = respuesta.get(
        "escalamiento",
        ""
    )

    if escalamiento:

        lineas.append("")
        lineas.append(
            "ESCALAMIENTO:"
        )

        lineas.append(
            escalamiento
        )

    return "\n".join(
        lineas
    )


# ==========================================================
# RESPUESTA PARA CÓDIGO
# ==========================================================

def construir_respuesta_codigo(
    registro
):

    lineas = []

    lineas.append(
        "CÓDIGO DE MANTENIMIENTO"
    )

    lineas.append("")

    lineas.append(
        f"Código: "
        f"{registro.get('codigo', '')}"
    )

    lineas.append(
        f"Significado: "
        f"{registro.get('significado', '')}"
    )

    tipo = registro.get(
        "tipo_mantenimiento",
        ""
    )

    if tipo:

        lineas.append(
            f"Tipo: {tipo}"
        )

    caso = registro.get(
        "aplicacion_o_caso",
        ""
    )

    if caso:

        lineas.append(
            f"Aplicación o caso: "
            f"{caso}"
        )

    accion = registro.get(
        "accion_asesor",
        ""
    )

    if accion:

        lineas.append("")
        lineas.append(
            "Acción del asesor:"
        )

        lineas.append(
            accion
        )

    observaciones = registro.get(
        "observaciones",
        ""
    )

    if observaciones:

        lineas.append("")
        lineas.append(
            "Observaciones:"
        )

        lineas.append(
            observaciones
        )

    return "\n".join(
        lineas
    )


# ==========================================================
# CONSULTA PRINCIPAL
# ==========================================================

def consultar(
    pregunta,
    base,
    mostrar_detalle=False
):

    # ------------------------------------------------------
    # PRIMERO BUSCAR CÓDIGOS
    # ------------------------------------------------------

    codigos = (
        buscar_codigo_mantenimiento(
            pregunta,
            base
        )
    )

    if codigos:

        return {
            "tipo": "codigo",
            "respuesta":
                construir_respuesta_codigo(
                    codigos[0]
                ),

            "resultados": codigos
        }

    # ------------------------------------------------------
    # BUSCAR PROCEDIMIENTOS
    # ------------------------------------------------------

    configuracion = base.get(
        "configuracion",
        {}
    )

    solo_activos = (
        configuracion.get(
            "solo_procedimientos_activos",
            True
        )
    )

    solo_validados = (
        configuracion.get(
            "solo_informacion_validada",
            False
        )
    )

    resultados = (
        buscar_procedimientos(
            pregunta,
            base,
            solo_activos,
            solo_validados
        )
    )

    if not resultados:

        return {
            "tipo": "sin_resultado",

            "respuesta":
                configuracion.get(
                    "respuesta_sin_resultado",
                    (
                        "No encuentro "
                        "información confirmada "
                        "para esta consulta."
                    )
                ),

            "resultados": []
        }

    mejor = resultados[0]

    procedimiento = (
        mejor[
            "procedimiento"
        ]
    )

    respuesta_texto = (
        construir_respuesta(
            procedimiento
        )
    )

    return {
        "tipo": "procedimiento",

        "respuesta":
            respuesta_texto,

        "procedimiento":
            procedimiento,

        "puntuacion":
            mejor[
                "puntuacion"
            ],

        "razones":
            mejor[
                "razones"
            ],

        "resultados":
            resultados
    }


# ==========================================================
# PRUEBA DIRECTA
# ==========================================================

if __name__ == "__main__":

    base = cargar_base()

    print()
    print("=" * 65)
    print(
        "MOTOR DE BÚSQUEDA "
        "- PRUEBA LOCAL"
    )
    print("=" * 65)

    print(
        "\nEscribe 'salir' "
        "para terminar."
    )

    while True:

        pregunta = input(
            "\nPregunta: "
        ).strip()

        if normalizar_texto(
            pregunta
        ) == "salir":

            print(
                "\nPrograma finalizado."
            )

            break

        if not pregunta:

            print(
                "Escribe una pregunta."
            )

            continue

        resultado = consultar(
            pregunta,
            base
        )

        print()
        print("-" * 65)
        print("RESPUESTA")
        print("-" * 65)

        print(
            resultado[
                "respuesta"
            ]
        )

        if (
            resultado[
                "tipo"
            ]
            ==
            "procedimiento"
        ):

            print()
            print("-" * 65)

            print(
                "Coincidencia seleccionada:"
            )

            print(
                resultado[
                    "procedimiento"
                ][
                    "id"
                ],
                "-",
                resultado[
                    "procedimiento"
                ][
                    "titulo"
                ]
            )

            print(
                "Puntuación:",
                resultado[
                    "puntuacion"
                ]
            )

            print()
            print(
                "Otros resultados:"
            )

            for item in (
                resultado[
                    "resultados"
                ]
            ):

                procedimiento = (
                    item[
                        "procedimiento"
                    ]
                )

                print(
                    f"- "
                    f"{procedimiento['id']} "
                    f"| "
                    f"{procedimiento['titulo']} "
                    f"| "
                    f"{item['puntuacion']}"
                )