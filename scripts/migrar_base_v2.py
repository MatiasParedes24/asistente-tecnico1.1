import json
import shutil
from pathlib import Path
from datetime import datetime


# ==========================================================
# RUTAS
# ==========================================================

RAIZ = Path(__file__).resolve().parent.parent

ARCHIVO_BD = (
    RAIZ
    / "data"
    / "base_conocimiento.json"
)

CARPETA_BACKUPS = (
    RAIZ
    / "data"
    / "backups"
)


# ==========================================================
# UTILIDADES
# ==========================================================

def cargar_json(ruta):

    with open(
        ruta,
        "r",
        encoding="utf-8"
    ) as archivo:

        return json.load(archivo)


def guardar_json(ruta, datos):

    with open(
        ruta,
        "w",
        encoding="utf-8"
    ) as archivo:

        json.dump(
            datos,
            archivo,
            ensure_ascii=False,
            indent=4
        )


def crear_backup():

    CARPETA_BACKUPS.mkdir(
        parents=True,
        exist_ok=True
    )

    fecha = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    destino = (
        CARPETA_BACKUPS
        / f"base_conocimiento_{fecha}.json"
    )

    shutil.copy2(
        ARCHIVO_BD,
        destino
    )

    return destino


def fecha_actual():

    return datetime.now().strftime(
        "%Y-%m-%d"
    )


# ==========================================================
# CONVERSIÓN DE PROCEDIMIENTOS
# ==========================================================

def convertir_pasos(pasos_antiguos):

    nuevos_pasos = []

    for indice, paso in enumerate(
        pasos_antiguos,
        start=1
    ):

        nuevos_pasos.append(
            {
                "orden": paso.get(
                    "orden",
                    indice
                ),

                "aplicativo": paso.get(
                    "aplicativo",
                    ""
                ),

                "accion": paso.get(
                    "accion",
                    ""
                ),

                "validacion": paso.get(
                    "validacion",
                    ""
                ),

                "si_no_cumple": paso.get(
                    "si_no_cumple",
                    ""
                )
            }
        )

    return nuevos_pasos


def convertir_procedimiento(
    procedimiento
):

    fecha = fecha_actual()

    nuevo = {

        "id": procedimiento.get(
            "id",
            ""
        ),

        "dominio": procedimiento.get(
            "dominio",
            ""
        ),

        "titulo": procedimiento.get(
            "titulo",
            ""
        ),

        "clasificacion": {

            "tipo_sot": procedimiento.get(
                "tipo_sot",
                []
            ),

            "tecnologia": procedimiento.get(
                "tecnologia",
                []
            ),

            "aplicativos": procedimiento.get(
                "aplicativos",
                []
            )
        },

        "busqueda": {

            "consultas_ejemplo": (
                procedimiento.get(
                    "intenciones",
                    []
                )
            ),

            "palabras_clave": (
                procedimiento.get(
                    "palabras_clave",
                    []
                )
            ),

            "sinonimos": []
        },

        "respuesta": {

            "resumen": procedimiento.get(
                "respuesta_corta",
                ""
            ),

            "pasos": convertir_pasos(
                procedimiento.get(
                    "pasos",
                    []
                )
            ),

            "precondiciones": (
                procedimiento.get(
                    "precondiciones",
                    []
                )
            ),

            "verificaciones": (
                procedimiento.get(
                    "evidencias",
                    []
                )
            ),

            "advertencias": (
                procedimiento.get(
                    "advertencias",
                    []
                )
            ),

            "accion_si_no_cumple": (
                procedimiento.get(
                    "accion_si_falla",
                    ""
                )
            ),

            "escalamiento": (
                procedimiento.get(
                    "escalamiento",
                    ""
                )
            )
        },

        "fuente": {

            "tipo": (
                "Capacitación interna"
            ),

            "referencia": (
                procedimiento.get(
                    "fuente_interna",
                    ""
                )
            )
        },

        "control": {

            "activo": procedimiento.get(
                "activo",
                True
            ),

            "validado": False,

            "fecha_creacion": fecha,

            "fecha_actualizacion": fecha
        }
    }

    return nuevo


# ==========================================================
# CÓDIGOS DE MANTENIMIENTO
# ==========================================================

def convertir_codigo(
    codigo_antiguo
):

    fecha = fecha_actual()

    return {

        "codigo": codigo_antiguo.get(
            "codigo",
            ""
        ),

        "significado": (
            codigo_antiguo.get(
                "significado",
                ""
            )
        ),

        "tipo_mantenimiento": (
            codigo_antiguo.get(
                "tipo_mantenimiento",
                ""
            )
        ),

        "aplicacion_o_caso": (
            codigo_antiguo.get(
                "aplicacion_o_caso",
                ""
            )
        ),

        "accion_asesor": (
            codigo_antiguo.get(
                "accion_asesor",
                ""
            )
        ),

        "observaciones": (
            codigo_antiguo.get(
                "observaciones",
                ""
            )
        ),

        "control": {

            "activo": codigo_antiguo.get(
                "activo",
                True
            ),

            "validado": False,

            "fecha_actualizacion": fecha
        }
    }


# ==========================================================
# MIGRACIÓN PRINCIPAL
# ==========================================================

def migrar():

    if not ARCHIVO_BD.exists():

        print(
            "\nERROR: No existe "
            "base_conocimiento.json"
        )

        return

    base_antigua = cargar_json(
        ARCHIVO_BD
    )

    version_actual = (
        base_antigua
        .get(
            "metadata",
            {}
        )
        .get(
            "version",
            "1.0"
        )
    )

    if str(version_actual).startswith(
        "2."
    ):

        print(
            "\nLa base ya utiliza "
            "la estructura versión 2."
        )

        return

    print(
        "\nSe realizará la migración "
        "de la base."
    )

    print(
        f"Versión encontrada: "
        f"{version_actual}"
    )

    confirmar = input(
        "\n¿Continuar? (s/n): "
    ).strip().lower()

    if confirmar != "s":

        print(
            "\nMigración cancelada."
        )

        return

    backup = crear_backup()

    print(
        "\nBackup creado:"
    )

    print(
        backup
    )

    procedimientos_nuevos = []

    for procedimiento in (
        base_antigua.get(
            "procedimientos",
            []
        )
    ):

        convertido = (
            convertir_procedimiento(
                procedimiento
            )
        )

        procedimientos_nuevos.append(
            convertido
        )

    codigos_nuevos = []

    for codigo in (
        base_antigua.get(
            "codigos_mantenimiento",
            []
        )
    ):

        codigos_nuevos.append(
            convertir_codigo(
                codigo
            )
        )

    nueva_base = {

        "metadata": {

            "nombre": (
                "Base de conocimiento "
                "- Asistente Técnico"
            ),

            "version": "2.0",

            "ultima_actualizacion": (
                fecha_actual()
            ),

            "descripcion": (
                "Base estructurada de "
                "procedimientos operativos "
                "para consulta del asistente."
            ),

            "politica_respuesta": (
                "El asistente debe responder "
                "únicamente utilizando "
                "información registrada "
                "y validada en esta base."
            )
        },

        "procedimientos": (
            procedimientos_nuevos
        ),

        "codigos_mantenimiento": (
            codigos_nuevos
        ),

        "configuracion": {

            "respuesta_sin_resultado": (
                "No encuentro información "
                "confirmada para esta consulta. "
                "Verifica el caso con tu "
                "supervisor."
            ),

            "max_resultados": 5,

            "solo_procedimientos_activos": (
                True
            ),

            "solo_informacion_validada": (
                False
            )
        }
    }

    guardar_json(
        ARCHIVO_BD,
        nueva_base
    )

    print()
    print("=" * 60)
    print(
        "MIGRACIÓN FINALIZADA"
    )
    print("=" * 60)

    print(
        f"Procedimientos migrados: "
        f"{len(procedimientos_nuevos)}"
    )

    print(
        f"Códigos migrados: "
        f"{len(codigos_nuevos)}"
    )

    print(
        "\nNueva versión: 2.0"
    )


# ==========================================================
# INICIO
# ==========================================================

if __name__ == "__main__":

    migrar()