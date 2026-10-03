import json
import unicodedata
from pathlib import Path
from datetime import datetime


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
# UTILIDADES GENERALES
# ==========================================================

def fecha_actual():

    return datetime.now().strftime(
        "%Y-%m-%d"
    )


def cargar_base():

    if not ARCHIVO_BD.exists():

        print(
            "\nERROR: No existe "
            "base_conocimiento.json"
        )

        return None

    try:

        with open(
            ARCHIVO_BD,
            "r",
            encoding="utf-8"
        ) as archivo:

            return json.load(
                archivo
            )

    except json.JSONDecodeError as error:

        print(
            "\nERROR EN JSON:"
        )

        print(
            f"Línea {error.lineno}, "
            f"columna {error.colno}"
        )

        return None


def guardar_base(base):

    base[
        "metadata"
    ][
        "ultima_actualizacion"
    ] = fecha_actual()

    with open(
        ARCHIVO_BD,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            base,
            archivo,
            ensure_ascii=False,
            indent=4
        )

    print(
        "\n✅ Cambios guardados."
    )


def normalizar(texto):

    texto = str(
        texto
    ).lower().strip()

    texto = "".join(
        caracter
        for caracter
        in unicodedata.normalize(
            "NFD",
            texto
        )
        if unicodedata.category(
            caracter
        ) != "Mn"
    )

    return texto


def pedir_lista(
    mensaje,
    separador=","
):

    texto = input(
        mensaje
    ).strip()

    if not texto:

        return []

    return [
        elemento.strip()
        for elemento
        in texto.split(
            separador
        )
        if elemento.strip()
    ]


def pedir_si_no(
    mensaje
):

    while True:

        opcion = input(
            f"{mensaje} (s/n): "
        ).strip().lower()

        if opcion == "s":
            return True

        if opcion == "n":
            return False

        print(
            "Solo ingresa s o n."
        )


def pausar():

    input(
        "\nPresiona ENTER "
        "para continuar..."
    )


# ==========================================================
# IDENTIFICADORES
# ==========================================================

def prefijo_por_dominio(
    dominio
):

    mapa = {

        "validacion": "VAL",

        "reprogramacion": "REP",

        "rechazo": "REC",

        "activacion": "ACT",

        "mantenimiento": "MAN",

        "instalacion": "INS",

        "migracion": "MIG",

        "programacion": "PRO"
    }

    return mapa.get(
        normalizar(
            dominio
        ),
        "GEN"
    )


def siguiente_id(
    base,
    dominio
):

    prefijo = (
        prefijo_por_dominio(
            dominio
        )
    )

    numeros = []

    for procedimiento in (
        base.get(
            "procedimientos",
            []
        )
    ):

        identificador = (
            procedimiento.get(
                "id",
                ""
            )
        )

        if identificador.startswith(
            prefijo
        ):

            numero = identificador[
                len(prefijo):
            ]

            if numero.isdigit():

                numeros.append(
                    int(numero)
                )

    siguiente = (
        max(
            numeros,
            default=0
        )
        + 1
    )

    return (
        f"{prefijo}"
        f"{siguiente:03d}"
    )


# ==========================================================
# BUSCAR PROCEDIMIENTO POR ID
# ==========================================================

def obtener_procedimiento(
    base,
    identificador
):

    for procedimiento in (
        base.get(
            "procedimientos",
            []
        )
    ):

        if (
            procedimiento.get(
                "id",
                ""
            ).upper()
            ==
            identificador.upper()
        ):

            return procedimiento

    return None


# ==========================================================
# LISTAR PROCEDIMIENTOS
# ==========================================================

def listar_procedimientos(
    base
):

    procedimientos = (
        base.get(
            "procedimientos",
            []
        )
    )

    print()
    print("=" * 100)
    print(
        "PROCEDIMIENTOS REGISTRADOS"
    )
    print("=" * 100)

    if not procedimientos:

        print(
            "No hay procedimientos."
        )

        return

    for procedimiento in (
        procedimientos
    ):

        control = (
            procedimiento.get(
                "control",
                {}
            )
        )

        activo = (
            "ACTIVO"
            if control.get(
                "activo",
                True
            )
            else "INACTIVO"
        )

        validado = (
            "VALIDADO"
            if control.get(
                "validado",
                False
            )
            else "PENDIENTE"
        )

        print(
            f"{procedimiento.get('id', ''):<8}"
            f"{procedimiento.get('dominio', ''):<20}"
            f"{procedimiento.get('titulo', ''):<45}"
            f"{activo:<12}"
            f"{validado}"
        )


# ==========================================================
# MOSTRAR PROCEDIMIENTO
# ==========================================================

def mostrar_lista(
    titulo,
    elementos
):

    print(
        f"\n{titulo}:"
    )

    if not elementos:

        print(
            "- Sin información"
        )

        return

    for elemento in elementos:

        print(
            f"- {elemento}"
        )


def mostrar_procedimiento(
    procedimiento
):

    print()
    print("=" * 80)

    print(
        f"{procedimiento.get('id', '')} "
        f"- "
        f"{procedimiento.get('titulo', '')}"
    )

    print("=" * 80)

    print(
        "\nDominio:",
        procedimiento.get(
            "dominio",
            ""
        )
    )

    clasificacion = (
        procedimiento.get(
            "clasificacion",
            {}
        )
    )

    mostrar_lista(
        "Tipo de SOT",
        clasificacion.get(
            "tipo_sot",
            []
        )
    )

    mostrar_lista(
        "Tecnología",
        clasificacion.get(
            "tecnologia",
            []
        )
    )

    mostrar_lista(
        "Aplicativos",
        clasificacion.get(
            "aplicativos",
            []
        )
    )

    busqueda = procedimiento.get(
        "busqueda",
        {}
    )

    mostrar_lista(
        "Consultas de ejemplo",
        busqueda.get(
            "consultas_ejemplo",
            []
        )
    )

    mostrar_lista(
        "Palabras clave",
        busqueda.get(
            "palabras_clave",
            []
        )
    )

    mostrar_lista(
        "Sinónimos",
        busqueda.get(
            "sinonimos",
            []
        )
    )

    respuesta = procedimiento.get(
        "respuesta",
        {}
    )

    print(
        "\nRespuesta:"
    )

    print(
        respuesta.get(
            "resumen",
            ""
        )
    )

    print(
        "\nPasos:"
    )

    pasos = respuesta.get(
        "pasos",
        []
    )

    if not pasos:

        print(
            "- Sin pasos registrados"
        )

    else:

        for paso in sorted(
            pasos,
            key=lambda x: x.get(
                "orden",
                0
            )
        ):

            print(
                f"{paso.get('orden')}. "
                f"[{paso.get('aplicativo', '')}] "
                f"{paso.get('accion', '')}"
            )

            if paso.get(
                "validacion"
            ):

                print(
                    "   Verificar: "
                    f"{paso.get('validacion')}"
                )

            if paso.get(
                "si_no_cumple"
            ):

                print(
                    "   Si no cumple: "
                    f"{paso.get('si_no_cumple')}"
                )

    mostrar_lista(
        "Precondiciones",
        respuesta.get(
            "precondiciones",
            []
        )
    )

    mostrar_lista(
        "Verificaciones",
        respuesta.get(
            "verificaciones",
            []
        )
    )

    mostrar_lista(
        "Advertencias",
        respuesta.get(
            "advertencias",
            []
        )
    )

    print(
        "\nAcción si no cumple:"
    )

    print(
        respuesta.get(
            "accion_si_no_cumple",
            ""
        )
        or
        "Sin información"
    )

    print(
        "\nEscalamiento:"
    )

    print(
        respuesta.get(
            "escalamiento",
            ""
        )
        or
        "Sin información"
    )

    fuente = procedimiento.get(
        "fuente",
        {}
    )

    print(
        "\nFuente:"
    )

    print(
        f"{fuente.get('tipo', '')} - "
        f"{fuente.get('referencia', '')}"
    )

    control = procedimiento.get(
        "control",
        {}
    )

    print(
        "\nActivo:",
        control.get(
            "activo",
            True
        )
    )

    print(
        "Validado:",
        control.get(
            "validado",
            False
        )
    )

    print(
        "Fecha actualización:",
        control.get(
            "fecha_actualizacion",
            ""
        )
    )


# ==========================================================
# BUSCAR PROCEDIMIENTOS
# ==========================================================

def buscar_procedimientos(
    base
):

    consulta = input(
        "\nTexto a buscar: "
    ).strip()

    consulta_normalizada = (
        normalizar(
            consulta
        )
    )

    resultados = []

    for procedimiento in (
        base.get(
            "procedimientos",
            []
        )
    ):

        contenido = [
            procedimiento.get(
                "id",
                ""
            ),
            procedimiento.get(
                "titulo",
                ""
            ),
            procedimiento.get(
                "dominio",
                ""
            )
        ]

        clasificacion = (
            procedimiento.get(
                "clasificacion",
                {}
            )
        )

        contenido.extend(
            clasificacion.get(
                "tipo_sot",
                []
            )
        )

        contenido.extend(
            clasificacion.get(
                "tecnologia",
                []
            )
        )

        contenido.extend(
            clasificacion.get(
                "aplicativos",
                []
            )
        )

        busqueda = procedimiento.get(
            "busqueda",
            {}
        )

        contenido.extend(
            busqueda.get(
                "consultas_ejemplo",
                []
            )
        )

        contenido.extend(
            busqueda.get(
                "palabras_clave",
                []
            )
        )

        contenido.extend(
            busqueda.get(
                "sinonimos",
                []
            )
        )

        texto_total = (
            normalizar(
                " ".join(
                    contenido
                )
            )
        )

        if (
            consulta_normalizada
            in texto_total
        ):

            resultados.append(
                procedimiento
            )

    print()

    if not resultados:

        print(
            "No se encontraron "
            "procedimientos."
        )

        return

    for procedimiento in (
        resultados
    ):

        print(
            f"{procedimiento['id']} "
            f"- "
            f"{procedimiento['titulo']}"
        )


# ==========================================================
# CREAR PASOS
# ==========================================================

def crear_pasos():

    pasos = []

    while True:

        orden = len(
            pasos
        ) + 1

        print(
            f"\nPASO {orden}"
        )

        aplicativo = input(
            "Aplicativo: "
        ).strip()

        accion = input(
            "Acción: "
        ).strip()

        if not accion:

            print(
                "La acción es obligatoria."
            )

            continue

        validacion = input(
            "Qué verificar "
            "(opcional): "
        ).strip()

        si_no_cumple = input(
            "Qué hacer si no cumple "
            "(opcional): "
        ).strip()

        pasos.append(
            {
                "orden": orden,
                "aplicativo": aplicativo,
                "accion": accion,
                "validacion": validacion,
                "si_no_cumple": (
                    si_no_cumple
                )
            }
        )

        if not pedir_si_no(
            "¿Agregar otro paso?"
        ):

            break

    return pasos


# ==========================================================
# AGREGAR PROCEDIMIENTO
# ==========================================================

def agregar_procedimiento(
    base
):

    print()
    print("=" * 60)
    print(
        "NUEVO PROCEDIMIENTO"
    )
    print("=" * 60)

    dominio = input(
        "Dominio: "
    ).strip()

    if not dominio:

        print(
            "Dominio obligatorio."
        )

        return

    titulo = input(
        "Título: "
    ).strip()

    if not titulo:

        print(
            "Título obligatorio."
        )

        return

    identificador = (
        siguiente_id(
            base,
            dominio
        )
    )

    print(
        f"\nID asignado: "
        f"{identificador}"
    )

    tipo_sot = pedir_lista(
        "Tipos de SOT "
        "separados por coma: "
    )

    tecnologia = pedir_lista(
        "Tecnologías "
        "separadas por coma: "
    )

    aplicativos = pedir_lista(
        "Aplicativos "
        "separados por coma: "
    )

    consultas = pedir_lista(
        "Ejemplos de preguntas "
        "separados por |: ",
        "|"
    )

    palabras = pedir_lista(
        "Palabras clave "
        "separadas por coma: "
    )

    sinonimos = pedir_lista(
        "Sinónimos o expresiones "
        "equivalentes separados "
        "por coma: "
    )

    resumen = input(
        "Respuesta resumida: "
    ).strip()

    precondiciones = pedir_lista(
        "Precondiciones "
        "separadas por |: ",
        "|"
    )

    verificaciones = pedir_lista(
        "Verificaciones/evidencias "
        "separadas por |: ",
        "|"
    )

    advertencias = pedir_lista(
        "Advertencias "
        "separadas por |: ",
        "|"
    )

    accion_no_cumple = input(
        "Acción si no cumple: "
    ).strip()

    escalamiento = input(
        "Escalamiento "
        "(opcional): "
    ).strip()

    referencia = input(
        "Referencia de capacitación: "
    ).strip()

    pasos = []

    if pedir_si_no(
        "¿Registrar pasos?"
    ):

        pasos = crear_pasos()

    fecha = fecha_actual()

    procedimiento = {

        "id": identificador,

        "dominio": dominio,

        "titulo": titulo,

        "clasificacion": {

            "tipo_sot": tipo_sot,

            "tecnologia": tecnologia,

            "aplicativos": aplicativos
        },

        "busqueda": {

            "consultas_ejemplo": (
                consultas
            ),

            "palabras_clave": (
                palabras
            ),

            "sinonimos": (
                sinonimos
            )
        },

        "respuesta": {

            "resumen": resumen,

            "pasos": pasos,

            "precondiciones": (
                precondiciones
            ),

            "verificaciones": (
                verificaciones
            ),

            "advertencias": (
                advertencias
            ),

            "accion_si_no_cumple": (
                accion_no_cumple
            ),

            "escalamiento": (
                escalamiento
            )
        },

        "fuente": {

            "tipo": (
                "Capacitación interna"
            ),

            "referencia": referencia
        },

        "control": {

            "activo": True,

            "validado": False,

            "fecha_creacion": fecha,

            "fecha_actualizacion": fecha
        }
    }

    mostrar_procedimiento(
        procedimiento
    )

    if pedir_si_no(
        "\n¿Guardar procedimiento?"
    ):

        base[
            "procedimientos"
        ].append(
            procedimiento
        )

        guardar_base(
            base
        )


# ==========================================================
# EDITAR PROCEDIMIENTO
# ==========================================================

def editar_procedimiento(
    base
):

    identificador = input(
        "\nID del procedimiento: "
    ).strip()

    procedimiento = (
        obtener_procedimiento(
            base,
            identificador
        )
    )

    if not procedimiento:

        print(
            "Procedimiento "
            "no encontrado."
        )

        return

    while True:

        mostrar_procedimiento(
            procedimiento
        )

        print()
        print(
            "1. Título"
        )
        print(
            "2. Dominio"
        )
        print(
            "3. Tipo de SOT"
        )
        print(
            "4. Tecnología"
        )
        print(
            "5. Aplicativos"
        )
        print(
            "6. Consultas ejemplo"
        )
        print(
            "7. Palabras clave"
        )
        print(
            "8. Sinónimos"
        )
        print(
            "9. Respuesta resumida"
        )
        print(
            "10. Precondiciones"
        )
        print(
            "11. Verificaciones"
        )
        print(
            "12. Advertencias"
        )
        print(
            "13. Acción si no cumple"
        )
        print(
            "14. Escalamiento"
        )
        print(
            "15. Referencia"
        )
        print(
            "16. Reemplazar pasos"
        )
        print(
            "17. Finalizar"
        )

        opcion = input(
            "\nOpción: "
        ).strip()

        clasificacion = (
            procedimiento[
                "clasificacion"
            ]
        )

        busqueda = (
            procedimiento[
                "busqueda"
            ]
        )

        respuesta = (
            procedimiento[
                "respuesta"
            ]
        )

        if opcion == "1":

            procedimiento[
                "titulo"
            ] = input(
                "Nuevo título: "
            ).strip()

        elif opcion == "2":

            procedimiento[
                "dominio"
            ] = input(
                "Nuevo dominio: "
            ).strip()

        elif opcion == "3":

            clasificacion[
                "tipo_sot"
            ] = pedir_lista(
                "Tipos: "
            )

        elif opcion == "4":

            clasificacion[
                "tecnologia"
            ] = pedir_lista(
                "Tecnologías: "
            )

        elif opcion == "5":

            clasificacion[
                "aplicativos"
            ] = pedir_lista(
                "Aplicativos: "
            )

        elif opcion == "6":

            busqueda[
                "consultas_ejemplo"
            ] = pedir_lista(
                "Preguntas separadas por |: ",
                "|"
            )

        elif opcion == "7":

            busqueda[
                "palabras_clave"
            ] = pedir_lista(
                "Palabras clave: "
            )

        elif opcion == "8":

            busqueda[
                "sinonimos"
            ] = pedir_lista(
                "Sinónimos: "
            )

        elif opcion == "9":

            respuesta[
                "resumen"
            ] = input(
                "Respuesta: "
            ).strip()

        elif opcion == "10":

            respuesta[
                "precondiciones"
            ] = pedir_lista(
                "Precondiciones: ",
                "|"
            )

        elif opcion == "11":

            respuesta[
                "verificaciones"
            ] = pedir_lista(
                "Verificaciones: ",
                "|"
            )

        elif opcion == "12":

            respuesta[
                "advertencias"
            ] = pedir_lista(
                "Advertencias: ",
                "|"
            )

        elif opcion == "13":

            respuesta[
                "accion_si_no_cumple"
            ] = input(
                "Acción: "
            ).strip()

        elif opcion == "14":

            respuesta[
                "escalamiento"
            ] = input(
                "Escalamiento: "
            ).strip()

        elif opcion == "15":

            procedimiento[
                "fuente"
            ][
                "referencia"
            ] = input(
                "Referencia: "
            ).strip()

        elif opcion == "16":

            respuesta[
                "pasos"
            ] = crear_pasos()

        elif opcion == "17":

            procedimiento[
                "control"
            ][
                "fecha_actualizacion"
            ] = fecha_actual()

            guardar_base(
                base
            )

            break

        else:

            print(
                "Opción incorrecta."
            )


# ==========================================================
# CAMBIAR ESTADO
# ==========================================================

def cambiar_activo(
    base
):

    identificador = input(
        "\nID: "
    ).strip()

    procedimiento = (
        obtener_procedimiento(
            base,
            identificador
        )
    )

    if not procedimiento:

        print(
            "No encontrado."
        )

        return

    control = procedimiento[
        "control"
    ]

    control[
        "activo"
    ] = not control.get(
        "activo",
        True
    )

    control[
        "fecha_actualizacion"
    ] = fecha_actual()

    guardar_base(
        base
    )

    print(
        "\nEstado:",
        "ACTIVO"
        if control["activo"]
        else "INACTIVO"
    )


def cambiar_validado(
    base
):

    identificador = input(
        "\nID: "
    ).strip()

    procedimiento = (
        obtener_procedimiento(
            base,
            identificador
        )
    )

    if not procedimiento:

        print(
            "No encontrado."
        )

        return

    control = procedimiento[
        "control"
    ]

    control[
        "validado"
    ] = not control.get(
        "validado",
        False
    )

    control[
        "fecha_actualizacion"
    ] = fecha_actual()

    guardar_base(
        base
    )

    print(
        "\nValidación:",
        "VALIDADO"
        if control[
            "validado"
        ]
        else "PENDIENTE"
    )


# ==========================================================
# CÓDIGOS DE MANTENIMIENTO
# ==========================================================

def listar_codigos(
    base
):

    codigos = base.get(
        "codigos_mantenimiento",
        []
    )

    print()
    print(
        "CÓDIGOS DE MANTENIMIENTO"
    )

    if not codigos:

        print(
            "\nNo hay códigos "
            "registrados."
        )

        return

    for codigo in codigos:

        print(
            f"\n{codigo.get('codigo')} "
            f"- "
            f"{codigo.get('significado')}"
        )


def codigo_existe(
    base,
    codigo
):

    for registro in base.get(
        "codigos_mantenimiento",
        []
    ):

        if (
            registro.get(
                "codigo",
                ""
            ).upper()
            ==
            codigo.upper()
        ):

            return True

    return False


def agregar_codigo(
    base
):

    codigo = input(
        "\nCódigo: "
    ).strip().upper()

    if not codigo:

        print(
            "Código obligatorio."
        )

        return

    if codigo_existe(
        base,
        codigo
    ):

        print(
            "Ese código ya existe."
        )

        return

    significado = input(
        "Significado: "
    ).strip()

    tipo = input(
        "Tipo de mantenimiento: "
    ).strip()

    caso = input(
        "Aplicación o caso: "
    ).strip()

    accion = input(
        "Acción del asesor: "
    ).strip()

    observaciones = input(
        "Observaciones: "
    ).strip()

    registro = {

        "codigo": codigo,

        "significado": significado,

        "tipo_mantenimiento": tipo,

        "aplicacion_o_caso": caso,

        "accion_asesor": accion,

        "observaciones": observaciones,

        "control": {

            "activo": True,

            "validado": False,

            "fecha_actualizacion": (
                fecha_actual()
            )
        }
    }

    if pedir_si_no(
        "¿Guardar código?"
    ):

        base.setdefault(
            "codigos_mantenimiento",
            []
        ).append(
            registro
        )

        guardar_base(
            base
        )


# ==========================================================
# MENÚ PRINCIPAL
# ==========================================================

def menu():

    base = cargar_base()

    if base is None:

        return

    while True:

        print()
        print("=" * 60)
        print(
            "GESTOR DE BASE "
            "DE CONOCIMIENTO"
        )
        print("=" * 60)

        print(
            "1. Listar procedimientos"
        )

        print(
            "2. Buscar procedimiento"
        )

        print(
            "3. Ver procedimiento"
        )

        print(
            "4. Agregar procedimiento"
        )

        print(
            "5. Editar procedimiento"
        )

        print(
            "6. Activar / desactivar"
        )

        print(
            "7. Marcar validado / pendiente"
        )

        print(
            "8. Listar códigos "
            "de mantenimiento"
        )

        print(
            "9. Agregar código "
            "de mantenimiento"
        )

        print(
            "10. Salir"
        )

        opcion = input(
            "\nSeleccione opción: "
        ).strip()

        if opcion == "1":

            listar_procedimientos(
                base
            )

            pausar()

        elif opcion == "2":

            buscar_procedimientos(
                base
            )

            pausar()

        elif opcion == "3":

            identificador = input(
                "\nID: "
            ).strip()

            procedimiento = (
                obtener_procedimiento(
                    base,
                    identificador
                )
            )

            if procedimiento:

                mostrar_procedimiento(
                    procedimiento
                )

            else:

                print(
                    "No encontrado."
                )

            pausar()

        elif opcion == "4":

            agregar_procedimiento(
                base
            )

            base = cargar_base()

            pausar()

        elif opcion == "5":

            editar_procedimiento(
                base
            )

            base = cargar_base()

            pausar()

        elif opcion == "6":

            cambiar_activo(
                base
            )

            base = cargar_base()

            pausar()

        elif opcion == "7":

            cambiar_validado(
                base
            )

            base = cargar_base()

            pausar()

        elif opcion == "8":

            listar_codigos(
                base
            )

            pausar()

        elif opcion == "9":

            agregar_codigo(
                base
            )

            base = cargar_base()

            pausar()

        elif opcion == "10":

            print(
                "\nPrograma finalizado."
            )

            break

        else:

            print(
                "\nOpción incorrecta."
            )


# ==========================================================
# INICIO
# ==========================================================

if __name__ == "__main__":

    menu()