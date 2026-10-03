import json
import unicodedata
from pathlib import Path
from datetime import datetime


# ==========================================================
# RUTAS
# ==========================================================

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO_BD = RAIZ / "data" / "base_conocimiento.json"


# ==========================================================
# CARGAR Y GUARDAR BASE
# ==========================================================

def cargar_base():

    if not ARCHIVO_BD.exists():
        print("\nERROR: No existe base_conocimiento.json")
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

    print("\nCambios guardados correctamente.")


# ==========================================================
# UTILIDADES
# ==========================================================

def normalizar(texto):

    texto = str(texto).lower().strip()

    texto = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caracter) != "Mn"
    )

    return texto


def pedir_lista(mensaje, separador=","):

    valor = input(mensaje).strip()

    if not valor:
        return []

    return [
        elemento.strip()
        for elemento in valor.split(separador)
        if elemento.strip()
    ]


def pedir_si_no(mensaje):

    while True:

        respuesta = input(
            f"{mensaje} (s/n): "
        ).strip().lower()

        if respuesta in ["s", "n"]:
            return respuesta == "s"

        print("Ingresa solamente s o n.")


def pausar():
    input("\nPresiona ENTER para continuar...")


# ==========================================================
# IDs AUTOMÁTICOS
# ==========================================================

def obtener_prefijo(dominio):

    mapa = {
        "validacion": "VAL",
        "reprogramacion": "REP",
        "rechazo": "REC",
        "activacion": "ACT",
        "instalacion": "INS",
        "mantenimiento": "MAN",
        "programacion": "PRO",
        "migracion": "MIG"
    }

    return mapa.get(
        normalizar(dominio),
        "GEN"
    )


def siguiente_id(base, dominio):

    prefijo = obtener_prefijo(dominio)

    numeros = []

    for procedimiento in base["procedimientos"]:

        identificador = procedimiento.get(
            "id",
            ""
        )

        if identificador.startswith(prefijo):

            numero = identificador.replace(
                prefijo,
                ""
            )

            if numero.isdigit():
                numeros.append(int(numero))

    siguiente = max(numeros, default=0) + 1

    return f"{prefijo}{siguiente:03d}"


# ==========================================================
# VALIDACIONES
# ==========================================================

def validar_procedimiento(procedimiento):

    errores = []

    if not procedimiento.get("titulo"):
        errores.append(
            "El procedimiento no tiene título."
        )

    if not procedimiento.get("dominio"):
        errores.append(
            "El procedimiento no tiene dominio."
        )

    if not procedimiento.get("respuesta_corta"):
        errores.append(
            "El procedimiento no tiene respuesta corta."
        )

    if not procedimiento.get("palabras_clave"):
        errores.append(
            "No tiene palabras clave."
        )

    if not procedimiento.get("intenciones"):
        errores.append(
            "No tiene ejemplos de preguntas."
        )

    return errores


# ==========================================================
# LISTAR PROCEDIMIENTOS
# ==========================================================

def listar_procedimientos(base):

    procedimientos = base["procedimientos"]

    if not procedimientos:

        print(
            "\nNo hay procedimientos registrados."
        )

        return

    print("\n")
    print("=" * 90)
    print("PROCEDIMIENTOS REGISTRADOS")
    print("=" * 90)

    for procedimiento in procedimientos:

        estado = (
            "ACTIVO"
            if procedimiento.get(
                "activo",
                True
            )
            else "INACTIVO"
        )

        print(
            f"{procedimiento['id']:<8}"
            f"{procedimiento['dominio']:<20}"
            f"{procedimiento['titulo']:<50}"
            f"{estado}"
        )


# ==========================================================
# BUSCAR PROCEDIMIENTO
# ==========================================================

def buscar_procedimientos(base):

    consulta = input(
        "\nIngrese texto a buscar: "
    ).strip()

    consulta = normalizar(consulta)

    resultados = []

    for procedimiento in base["procedimientos"]:

        contenido = []

        contenido.append(
            procedimiento.get(
                "id",
                ""
            )
        )

        contenido.append(
            procedimiento.get(
                "titulo",
                ""
            )
        )

        contenido.append(
            procedimiento.get(
                "dominio",
                ""
            )
        )

        contenido.extend(
            procedimiento.get(
                "palabras_clave",
                []
            )
        )

        contenido.extend(
            procedimiento.get(
                "intenciones",
                []
            )
        )

        contenido.extend(
            procedimiento.get(
                "aplicativos",
                []
            )
        )

        texto_total = normalizar(
            " ".join(contenido)
        )

        if consulta in texto_total:
            resultados.append(
                procedimiento
            )

    if not resultados:

        print(
            "\nNo se encontraron coincidencias."
        )

        return []

    print("\nRESULTADOS:\n")

    for procedimiento in resultados:

        print(
            f"{procedimiento['id']} - "
            f"{procedimiento['titulo']}"
        )

    return resultados


# ==========================================================
# OBTENER PROCEDIMIENTO POR ID
# ==========================================================

def obtener_procedimiento(base, id_busqueda):

    for procedimiento in base["procedimientos"]:

        if (
            procedimiento.get("id", "").upper()
            ==
            id_busqueda.upper()
        ):
            return procedimiento

    return None


# ==========================================================
# MOSTRAR PROCEDIMIENTO COMPLETO
# ==========================================================

def mostrar_procedimiento(procedimiento):

    print("\n")
    print("=" * 80)
    print(
        f"{procedimiento['id']} - "
        f"{procedimiento['titulo']}"
    )
    print("=" * 80)

    print(
        f"\nDominio: "
        f"{procedimiento.get('dominio', '')}"
    )

    print(
        "Tipo de SOT: "
        + ", ".join(
            procedimiento.get(
                "tipo_sot",
                []
            )
        )
    )

    print(
        "Tecnología: "
        + ", ".join(
            procedimiento.get(
                "tecnologia",
                []
            )
        )
    )

    print(
        "Aplicativos: "
        + ", ".join(
            procedimiento.get(
                "aplicativos",
                []
            )
        )
    )

    print(
        "\nRespuesta corta:"
    )

    print(
        procedimiento.get(
            "respuesta_corta",
            ""
        )
    )

    print(
        "\nPalabras clave:"
    )

    for palabra in procedimiento.get(
        "palabras_clave",
        []
    ):
        print(f"- {palabra}")

    print(
        "\nEjemplos de preguntas:"
    )

    for pregunta in procedimiento.get(
        "intenciones",
        []
    ):
        print(f"- {pregunta}")

    print(
        "\nPrecondiciones:"
    )

    for condicion in procedimiento.get(
        "precondiciones",
        []
    ):
        print(f"- {condicion}")

    print(
        "\nPasos:"
    )

    pasos = procedimiento.get(
        "pasos",
        []
    )

    if pasos:

        pasos_ordenados = sorted(
            pasos,
            key=lambda x: x.get(
                "orden",
                0
            )
        )

        for paso in pasos_ordenados:

            print(
                f"{paso.get('orden')}. "
                f"[{paso.get('aplicativo', '')}] "
                f"{paso.get('accion', '')}"
            )

    else:

        print(
            "No hay pasos registrados."
        )

    print(
        "\nEvidencias:"
    )

    for evidencia in procedimiento.get(
        "evidencias",
        []
    ):
        print(f"- {evidencia}")

    print(
        "\nAcción si falla:"
    )

    print(
        procedimiento.get(
            "accion_si_falla",
            ""
        )
    )

    print(
        "\nAdvertencias:"
    )

    for advertencia in procedimiento.get(
        "advertencias",
        []
    ):
        print(
            f"- {advertencia}"
        )

    print(
        "\nFuente interna:"
    )

    print(
        procedimiento.get(
            "fuente_interna",
            ""
        )
    )

    print(
        "\nEstado:",
        "ACTIVO"
        if procedimiento.get(
            "activo",
            True
        )
        else "INACTIVO"
    )


# ==========================================================
# CREAR PROCEDIMIENTO
# ==========================================================

def agregar_procedimiento(base):

    print("\n")
    print("=" * 60)
    print("NUEVO PROCEDIMIENTO")
    print("=" * 60)

    dominio = input(
        "\nDominio: "
    ).strip()

    if not dominio:

        print(
            "El dominio es obligatorio."
        )

        return

    titulo = input(
        "Título: "
    ).strip()

    if not titulo:

        print(
            "El título es obligatorio."
        )

        return

    identificador = siguiente_id(
        base,
        dominio
    )

    print(
        f"\nID asignado automáticamente: "
        f"{identificador}"
    )

    tipo_sot = pedir_lista(
        "\nTipos de SOT separados por coma: "
    )

    tecnologia = pedir_lista(
        "Tecnologías separadas por coma: "
    )

    aplicativos = pedir_lista(
        "Aplicativos separados por coma: "
    )

    palabras_clave = pedir_lista(
        "Palabras clave separadas por coma: "
    )

    print(
        "\nEjemplos de preguntas."
    )

    print(
        "Sepáralas utilizando |"
    )

    intenciones = pedir_lista(
        "Preguntas: ",
        "|"
    )

    respuesta_corta = input(
        "\nRespuesta corta: "
    ).strip()

    precondiciones = pedir_lista(
        "\nPrecondiciones separadas por |: ",
        "|"
    )

    evidencias = pedir_lista(
        "Evidencias separadas por |: ",
        "|"
    )

    accion_si_falla = input(
        "Acción si falla: "
    ).strip()

    advertencias = pedir_lista(
        "Advertencias separadas por |: ",
        "|"
    )

    fuente = input(
        "Fuente interna: "
    ).strip()

    procedimiento = {

        "id": identificador,

        "dominio": dominio,

        "titulo": titulo,

        "tipo_sot": tipo_sot,

        "tecnologia": tecnologia,

        "aplicativos": aplicativos,

        "intenciones": intenciones,

        "palabras_clave": palabras_clave,

        "respuesta_corta":
            respuesta_corta,

        "pasos": [],

        "precondiciones":
            precondiciones,

        "evidencias":
            evidencias,

        "accion_si_falla":
            accion_si_falla,

        "advertencias":
            advertencias,

        "fuente_interna":
            fuente,

        "activo": True
    }

    print("\n")

    errores = validar_procedimiento(
        procedimiento
    )

    if errores:

        print(
            "ADVERTENCIAS DE VALIDACIÓN:"
        )

        for error in errores:

            print(
                f"- {error}"
            )

        continuar = pedir_si_no(
            "\n¿Deseas guardar de todas formas?"
        )

        if not continuar:
            print(
                "Operación cancelada."
            )
            return

    if pedir_si_no(
        "\n¿Deseas agregar pasos ahora?"
    ):

        agregar_pasos_a_objeto(
            procedimiento
        )

    print("\nRESUMEN DEL PROCEDIMIENTO")

    mostrar_procedimiento(
        procedimiento
    )

    if pedir_si_no(
        "\n¿Guardar procedimiento?"
    ):

        base["procedimientos"].append(
            procedimiento
        )

        guardar_base(base)

        print(
            f"\nProcedimiento "
            f"{identificador} creado."
        )

    else:

        print(
            "\nOperación cancelada."
        )


# ==========================================================
# AGREGAR PASOS
# ==========================================================

def agregar_pasos_a_objeto(
    procedimiento
):

    print("\n")
    print(
        "AGREGAR PASOS"
    )

    while True:

        orden = (
            len(
                procedimiento.get(
                    "pasos",
                    []
                )
            )
            + 1
        )

        aplicativo = input(
            f"\nPaso {orden} - Aplicativo: "
        ).strip()

        accion = input(
            f"Paso {orden} - Acción: "
        ).strip()

        if not accion:

            print(
                "La acción no puede estar vacía."
            )

            continue

        nuevo_paso = {

            "orden": orden,

            "aplicativo":
                aplicativo,

            "accion":
                accion
        }

        procedimiento.setdefault(
            "pasos",
            []
        ).append(
            nuevo_paso
        )

        if not pedir_si_no(
            "\n¿Agregar otro paso?"
        ):
            break


def agregar_pasos_procedimiento(base):

    id_busqueda = input(
        "\nID del procedimiento: "
    ).strip()

    procedimiento = obtener_procedimiento(
        base,
        id_busqueda
    )

    if not procedimiento:

        print(
            "\nProcedimiento no encontrado."
        )

        return

    mostrar_procedimiento(
        procedimiento
    )

    agregar_pasos_a_objeto(
        procedimiento
    )

    guardar_base(base)


# ==========================================================
# EDITAR PROCEDIMIENTO
# ==========================================================

def editar_procedimiento(base):

    id_busqueda = input(
        "\nID del procedimiento a editar: "
    ).strip()

    procedimiento = obtener_procedimiento(
        base,
        id_busqueda
    )

    if not procedimiento:

        print(
            "\nProcedimiento no encontrado."
        )

        return

    mostrar_procedimiento(
        procedimiento
    )

    while True:

        print("\n")
        print("¿QUÉ DESEAS EDITAR?")
        print("1. Título")
        print("2. Dominio")
        print("3. Tipos de SOT")
        print("4. Tecnología")
        print("5. Aplicativos")
        print("6. Palabras clave")
        print("7. Ejemplos de preguntas")
        print("8. Respuesta corta")
        print("9. Precondiciones")
        print("10. Evidencias")
        print("11. Acción si falla")
        print("12. Advertencias")
        print("13. Fuente interna")
        print("14. Terminar edición")

        opcion = input(
            "\nSeleccione opción: "
        ).strip()

        if opcion == "1":

            procedimiento["titulo"] = (
                input(
                    "Nuevo título: "
                ).strip()
            )

        elif opcion == "2":

            procedimiento["dominio"] = (
                input(
                    "Nuevo dominio: "
                ).strip()
            )

        elif opcion == "3":

            procedimiento["tipo_sot"] = (
                pedir_lista(
                    "Tipos separados por coma: "
                )
            )

        elif opcion == "4":

            procedimiento["tecnologia"] = (
                pedir_lista(
                    "Tecnologías separadas por coma: "
                )
            )

        elif opcion == "5":

            procedimiento["aplicativos"] = (
                pedir_lista(
                    "Aplicativos separados por coma: "
                )
            )

        elif opcion == "6":

            procedimiento[
                "palabras_clave"
            ] = pedir_lista(
                "Palabras separadas por coma: "
            )

        elif opcion == "7":

            procedimiento[
                "intenciones"
            ] = pedir_lista(
                "Preguntas separadas por |: ",
                "|"
            )

        elif opcion == "8":

            procedimiento[
                "respuesta_corta"
            ] = input(
                "Nueva respuesta: "
            ).strip()

        elif opcion == "9":

            procedimiento[
                "precondiciones"
            ] = pedir_lista(
                "Precondiciones separadas por |: ",
                "|"
            )

        elif opcion == "10":

            procedimiento[
                "evidencias"
            ] = pedir_lista(
                "Evidencias separadas por |: ",
                "|"
            )

        elif opcion == "11":

            procedimiento[
                "accion_si_falla"
            ] = input(
                "Nueva acción si falla: "
            ).strip()

        elif opcion == "12":

            procedimiento[
                "advertencias"
            ] = pedir_lista(
                "Advertencias separadas por |: ",
                "|"
            )

        elif opcion == "13":

            procedimiento[
                "fuente_interna"
            ] = input(
                "Fuente interna: "
            ).strip()

        elif opcion == "14":
            break

        else:

            print(
                "Opción no válida."
            )

    guardar_base(base)


# ==========================================================
# ACTIVAR / DESACTIVAR
# ==========================================================

def cambiar_estado_procedimiento(base):

    id_busqueda = input(
        "\nID del procedimiento: "
    ).strip()

    procedimiento = obtener_procedimiento(
        base,
        id_busqueda
    )

    if not procedimiento:

        print(
            "Procedimiento no encontrado."
        )

        return

    estado_actual = procedimiento.get(
        "activo",
        True
    )

    procedimiento["activo"] = (
        not estado_actual
    )

    guardar_base(base)

    print(
        f"\nNuevo estado: "
        f"{'ACTIVO' if procedimiento['activo'] else 'INACTIVO'}"
    )


# ==========================================================
# CÓDIGOS DE MANTENIMIENTO
# ==========================================================

def listar_codigos(base):

    codigos = base.get(
        "codigos_mantenimiento",
        []
    )

    if not codigos:

        print(
            "\nNo hay códigos registrados."
        )

        return

    print("\nCÓDIGOS DE MANTENIMIENTO\n")

    for registro in codigos:

        print(
            f"{registro['codigo']} - "
            f"{registro['significado']}"
        )


def codigo_existe(base, codigo):

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


def agregar_codigo(base):

    print("\n")
    print("=" * 50)
    print("NUEVO CÓDIGO DE MANTENIMIENTO")
    print("=" * 50)

    codigo = input(
        "Código: "
    ).strip().upper()

    if not codigo:

        print(
            "El código es obligatorio."
        )

        return

    if codigo_existe(
        base,
        codigo
    ):

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
        "Acción del asesor: "
    ).strip()

    observaciones = input(
        "Observaciones: "
    ).strip()

    registro = {

        "codigo":
            codigo,

        "significado":
            significado,

        "tipo_mantenimiento":
            tipo,

        "aplicacion_o_caso":
            caso,

        "accion_asesor":
            accion,

        "observaciones":
            observaciones,

        "activo":
            True
    }

    if pedir_si_no(
        "\n¿Guardar código?"
    ):

        base.setdefault(
            "codigos_mantenimiento",
            []
        ).append(
            registro
        )

        guardar_base(base)

        print(
            f"\nCódigo {codigo} agregado."
        )


# ==========================================================
# ESTADÍSTICAS
# ==========================================================

def mostrar_estadisticas(base):

    procedimientos = base.get(
        "procedimientos",
        []
    )

    activos = sum(
        1
        for p in procedimientos
        if p.get(
            "activo",
            True
        )
    )

    inactivos = (
        len(procedimientos)
        - activos
    )

    codigos = len(
        base.get(
            "codigos_mantenimiento",
            []
        )
    )

    dominios = {}

    for procedimiento in procedimientos:

        dominio = procedimiento.get(
            "dominio",
            "sin dominio"
        )

        dominios[dominio] = (
            dominios.get(
                dominio,
                0
            )
            + 1
        )

    print("\n")
    print("=" * 50)
    print("ESTADÍSTICAS DE LA BASE")
    print("=" * 50)

    print(
        f"Procedimientos totales: "
        f"{len(procedimientos)}"
    )

    print(
        f"Activos: {activos}"
    )

    print(
        f"Inactivos: {inactivos}"
    )

    print(
        f"Códigos de mantenimiento: "
        f"{codigos}"
    )

    print(
        "\nProcedimientos por dominio:"
    )

    for dominio, cantidad in dominios.items():

        print(
            f"- {dominio}: {cantidad}"
        )


# ==========================================================
# MENÚ PRINCIPAL
# ==========================================================

def menu():

    base = cargar_base()

    if base is None:
        return

    while True:

        print("\n")
        print("=" * 60)
        print(
            "GESTIÓN DE BASE DE CONOCIMIENTO"
        )
        print("=" * 60)

        print(
            "1. Listar procedimientos"
        )

        print(
            "2. Buscar procedimiento"
        )

        print(
            "3. Ver procedimiento completo"
        )

        print(
            "4. Agregar procedimiento"
        )

        print(
            "5. Editar procedimiento"
        )

        print(
            "6. Agregar pasos a procedimiento"
        )

        print(
            "7. Activar / desactivar procedimiento"
        )

        print(
            "8. Listar códigos de mantenimiento"
        )

        print(
            "9. Agregar código de mantenimiento"
        )

        print(
            "10. Ver estadísticas"
        )

        print(
            "11. Salir"
        )

        opcion = input(
            "\nSeleccione una opción: "
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

            id_busqueda = input(
                "\nIngrese ID: "
            ).strip()

            procedimiento = (
                obtener_procedimiento(
                    base,
                    id_busqueda
                )
            )

            if procedimiento:

                mostrar_procedimiento(
                    procedimiento
                )

            else:

                print(
                    "Procedimiento no encontrado."
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

            agregar_pasos_procedimiento(
                base
            )

            base = cargar_base()

            pausar()

        elif opcion == "7":

            cambiar_estado_procedimiento(
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

            mostrar_estadisticas(
                base
            )

            pausar()

        elif opcion == "11":

            print(
                "\nPrograma finalizado."
            )

            break

        else:

            print(
                "\nOpción no válida."
            )


# ==========================================================
# INICIO
# ==========================================================

if __name__ == "__main__":
    menu()