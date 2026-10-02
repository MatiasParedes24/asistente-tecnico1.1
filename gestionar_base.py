import json
import unicodedata
from pathlib import Path
from datetime import datetime


RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO_BD = RAIZ / "data" / "base_conocimiento.json"


# ==========================================================
# UTILIDADES
# ==========================================================

def cargar_base():

    if not ARCHIVO_BD.exists():
        print("ERROR: No existe base_conocimiento.json")
        print("Ejecuta primero:")
        print("python scripts/crear_base.py")
        return None

    with open(
        ARCHIVO_BD,
        "r",
        encoding="utf-8"
    ) as archivo:
        return json.load(archivo)


def guardar_base(base):

    base["metadata"]["ultima_actualizacion"] = (
        datetime.now().strftime("%Y-%m-%d")
    )

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


def normalizar(texto):

    texto = texto.lower()

    texto = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caracter) != "Mn"
    )

    return texto.strip()


def siguiente_id(base, prefijo):

    numeros = []

    for procedimiento in base["procedimientos"]:

        identificador = procedimiento["id"]

        if identificador.startswith(prefijo):

            try:
                numeros.append(
                    int(identificador[len(prefijo):])
                )
            except ValueError:
                pass

    siguiente = max(numeros, default=0) + 1

    return f"{prefijo}{siguiente:03d}"


# ==========================================================
# PROCEDIMIENTOS
# ==========================================================

def listar_procedimientos(base):

    print("\nPROCEDIMIENTOS REGISTRADOS\n")

    for procedimiento in base["procedimientos"]:

        estado = (
            "ACTIVO"
            if procedimiento.get("activo", True)
            else "INACTIVO"
        )

        print(
            f"{procedimiento['id']} | "
            f"{procedimiento['dominio']} | "
            f"{procedimiento['titulo']} | "
            f"{estado}"
        )


def buscar_procedimiento(base):

    consulta = input(
        "\nIngrese palabra o texto a buscar: "
    )

    consulta = normalizar(consulta)

    resultados = []

    for procedimiento in base["procedimientos"]:

        contenido = " ".join([
            procedimiento.get("titulo", ""),
            procedimiento.get("dominio", ""),
            " ".join(
                procedimiento.get(
                    "palabras_clave",
                    []
                )
            ),
            " ".join(
                procedimiento.get(
                    "intenciones",
                    []
                )
            )
        ])

        if consulta in normalizar(contenido):
            resultados.append(procedimiento)

    if not resultados:
        print("\nNo se encontraron procedimientos.")
        return

    print()

    for procedimiento in resultados:

        print(
            f"{procedimiento['id']} - "
            f"{procedimiento['titulo']}"
        )


def agregar_procedimiento(base):

    print("\nNUEVO PROCEDIMIENTO")
    print("-----------------------------")

    dominio = input(
        "Dominio (validacion/reprogramacion/etc.): "
    ).strip().lower()

    titulo = input(
        "Título: "
    ).strip()

    if dominio == "validacion":
        prefijo = "VAL"

    elif dominio == "reprogramacion":
        prefijo = "REP"

    elif dominio == "rechazo":
        prefijo = "REC"

    else:
        prefijo = "GEN"

    identificador = siguiente_id(
        base,
        prefijo
    )

    aplicativos = input(
        "Aplicativos separados por coma: "
    )

    palabras = input(
        "Palabras clave separadas por coma: "
    )

    intenciones = input(
        "Ejemplos de preguntas separados por | : "
    )

    respuesta_corta = input(
        "Respuesta corta: "
    ).strip()

    procedimiento = {

        "id": identificador,
        "dominio": dominio,
        "titulo": titulo,

        "tipo_sot": [],
        "tecnologia": [],

        "aplicativos": [
            x.strip()
            for x in aplicativos.split(",")
            if x.strip()
        ],

        "intenciones": [
            x.strip()
            for x in intenciones.split("|")
            if x.strip()
        ],

        "palabras_clave": [
            x.strip()
            for x in palabras.split(",")
            if x.strip()
        ],

        "respuesta_corta": respuesta_corta,

        "pasos": [],

        "precondiciones": [],
        "evidencias": [],

        "accion_si_falla": "",
        "advertencias": [],

        "fuente_interna": (
            "Pendiente de registrar"
        ),

        "activo": True
    }

    print()
    print("Se creará:")
    print(
        f"{identificador} - {titulo}"
    )

    confirmar = input(
        "¿Guardar? (s/n): "
    ).lower()

    if confirmar != "s":
        print("Cancelado.")
        return

    base["procedimientos"].append(
        procedimiento
    )

    guardar_base(base)

    print(
        f"\nProcedimiento {identificador} "
        "creado correctamente."
    )


# ==========================================================
# CÓDIGOS DE MANTENIMIENTO
# ==========================================================

def agregar_codigo_mantenimiento(base):

    print("\nNUEVO CÓDIGO DE MANTENIMIENTO")
    print("-----------------------------")

    codigo = input(
        "Código: "
    ).strip().upper()

    # Evitar duplicados
    for registro in base["codigos_mantenimiento"]:

        if registro["codigo"].upper() == codigo:

            print(
                "\nERROR: Ese código ya existe."
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
        "Acción recomendada para el asesor: "
    ).strip()

    registro = {

        "codigo": codigo,
        "significado": significado,
        "tipo_mantenimiento": tipo,
        "aplicacion_o_caso": caso,
        "accion_asesor": accion,
        "observaciones": "",
        "activo": True
    }

    base["codigos_mantenimiento"].append(
        registro
    )

    guardar_base(base)

    print(
        f"\nCódigo {codigo} agregado."
    )


# ==========================================================
# MENÚ
# ==========================================================

def menu():

    base = cargar_base()

    if base is None:
        return

    while True:

        print("\n")
        print("=====================================")
        print(" GESTIÓN DE BASE DE CONOCIMIENTO")
        print("=====================================")
        print("1. Listar procedimientos")
        print("2. Buscar procedimiento")
        print("3. Agregar procedimiento")
        print("4. Agregar código de mantenimiento")
        print("5. Salir")

        opcion = input(
            "\nSeleccione una opción: "
        ).strip()

        if opcion == "1":
            listar_procedimientos(base)

        elif opcion == "2":
            buscar_procedimiento(base)

        elif opcion == "3":
            agregar_procedimiento(base)

            # Recargar por seguridad
            base = cargar_base()

        elif opcion == "4":
            agregar_codigo_mantenimiento(base)

            base = cargar_base()

        elif opcion == "5":
            print("\nPrograma finalizado.")
            break

        else:
            print(
                "\nOpción no válida."
            )


if __name__ == "__main__":
    menu()