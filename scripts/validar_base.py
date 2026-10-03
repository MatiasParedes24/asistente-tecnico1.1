import json
from pathlib import Path
from collections import Counter


# ==========================================================
# RUTA
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
# CARGAR BASE
# ==========================================================

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
            "\nERROR DE FORMATO JSON"
        )

        print(
            f"Línea: {error.lineno}"
        )

        print(
            f"Columna: {error.colno}"
        )

        print(
            error.msg
        )

        return None


# ==========================================================
# VALIDAR METADATA
# ==========================================================

def validar_metadata(
    base,
    errores,
    advertencias
):

    metadata = base.get(
        "metadata"
    )

    if not isinstance(
        metadata,
        dict
    ):

        errores.append(
            "No existe metadata."
        )

        return

    if not metadata.get(
        "version"
    ):

        errores.append(
            "metadata.version está vacío."
        )

    if not metadata.get(
        "nombre"
    ):

        advertencias.append(
            "metadata.nombre está vacío."
        )


# ==========================================================
# VALIDAR PROCEDIMIENTO
# ==========================================================

def validar_procedimiento(
    procedimiento,
    indice,
    errores,
    advertencias
):

    etiqueta = (
        procedimiento.get(
            "id",
            f"posición {indice}"
        )
    )

    # ------------------------------------------------------
    # CAMPOS PRINCIPALES
    # ------------------------------------------------------

    campos_obligatorios = [
        "id",
        "dominio",
        "titulo",
        "clasificacion",
        "busqueda",
        "respuesta",
        "fuente",
        "control"
    ]

    for campo in campos_obligatorios:

        if campo not in procedimiento:

            errores.append(
                f"{etiqueta}: "
                f"falta campo '{campo}'."
            )

    if not procedimiento.get(
        "id"
    ):

        errores.append(
            f"{etiqueta}: ID vacío."
        )

    if not procedimiento.get(
        "titulo"
    ):

        errores.append(
            f"{etiqueta}: título vacío."
        )

    if not procedimiento.get(
        "dominio"
    ):

        errores.append(
            f"{etiqueta}: dominio vacío."
        )

    # ------------------------------------------------------
    # CLASIFICACIÓN
    # ------------------------------------------------------

    clasificacion = (
        procedimiento.get(
            "clasificacion",
            {}
        )
    )

    for campo in [
        "tipo_sot",
        "tecnologia",
        "aplicativos"
    ]:

        valor = clasificacion.get(
            campo
        )

        if not isinstance(
            valor,
            list
        ):

            errores.append(
                f"{etiqueta}: "
                f"clasificacion."
                f"{campo} debe ser lista."
            )

    # ------------------------------------------------------
    # BÚSQUEDA
    # ------------------------------------------------------

    busqueda = procedimiento.get(
        "busqueda",
        {}
    )

    consultas = busqueda.get(
        "consultas_ejemplo",
        []
    )

    palabras = busqueda.get(
        "palabras_clave",
        []
    )

    sinonimos = busqueda.get(
        "sinonimos",
        []
    )

    if not isinstance(
        consultas,
        list
    ):

        errores.append(
            f"{etiqueta}: "
            "consultas_ejemplo "
            "debe ser lista."
        )

    if not isinstance(
        palabras,
        list
    ):

        errores.append(
            f"{etiqueta}: "
            "palabras_clave "
            "debe ser lista."
        )

    if not isinstance(
        sinonimos,
        list
    ):

        errores.append(
            f"{etiqueta}: "
            "sinonimos debe ser lista."
        )

    if not consultas:

        advertencias.append(
            f"{etiqueta}: "
            "no tiene consultas de ejemplo."
        )

    if not palabras:

        advertencias.append(
            f"{etiqueta}: "
            "no tiene palabras clave."
        )

    # ------------------------------------------------------
    # RESPUESTA
    # ------------------------------------------------------

    respuesta = procedimiento.get(
        "respuesta",
        {}
    )

    if not respuesta.get(
        "resumen"
    ):

        errores.append(
            f"{etiqueta}: "
            "respuesta.resumen está vacío."
        )

    pasos = respuesta.get(
        "pasos",
        []
    )

    if not isinstance(
        pasos,
        list
    ):

        errores.append(
            f"{etiqueta}: "
            "respuesta.pasos debe ser lista."
        )

    else:

        ordenes = []

        for paso in pasos:

            orden = paso.get(
                "orden"
            )

            accion = paso.get(
                "accion"
            )

            if orden is None:

                errores.append(
                    f"{etiqueta}: "
                    "hay un paso sin orden."
                )

            else:

                ordenes.append(
                    orden
                )

            if not accion:

                errores.append(
                    f"{etiqueta}: "
                    "hay un paso sin acción."
                )

        duplicados = [
            orden
            for orden, cantidad
            in Counter(
                ordenes
            ).items()
            if cantidad > 1
        ]

        if duplicados:

            errores.append(
                f"{etiqueta}: "
                f"órdenes de paso "
                f"duplicados: "
                f"{duplicados}"
            )

    # ------------------------------------------------------
    # CONTROL
    # ------------------------------------------------------

    control = procedimiento.get(
        "control",
        {}
    )

    if not isinstance(
        control.get(
            "activo",
            True
        ),
        bool
    ):

        errores.append(
            f"{etiqueta}: "
            "control.activo "
            "debe ser true/false."
        )

    if not isinstance(
        control.get(
            "validado",
            False
        ),
        bool
    ):

        errores.append(
            f"{etiqueta}: "
            "control.validado "
            "debe ser true/false."
        )

    # ------------------------------------------------------
    # FUENTE
    # ------------------------------------------------------

    fuente = procedimiento.get(
        "fuente",
        {}
    )

    if not fuente.get(
        "referencia"
    ):

        advertencias.append(
            f"{etiqueta}: "
            "no tiene referencia "
            "de fuente interna."
        )


# ==========================================================
# VALIDAR IDs DUPLICADOS
# ==========================================================

def validar_ids(
    procedimientos,
    errores
):

    ids = [
        p.get(
            "id"
        )
        for p
        in procedimientos
        if p.get(
            "id"
        )
    ]

    contador = Counter(
        ids
    )

    duplicados = [
        identificador
        for identificador, cantidad
        in contador.items()
        if cantidad > 1
    ]

    for identificador in duplicados:

        errores.append(
            f"ID duplicado: "
            f"{identificador}"
        )


# ==========================================================
# VALIDAR CÓDIGOS
# ==========================================================

def validar_codigos(
    base,
    errores,
    advertencias
):

    codigos = base.get(
        "codigos_mantenimiento",
        []
    )

    encontrados = []

    for registro in codigos:

        codigo = registro.get(
            "codigo",
            ""
        ).strip()

        if not codigo:

            errores.append(
                "Existe un código "
                "de mantenimiento vacío."
            )

            continue

        encontrados.append(
            codigo.upper()
        )

        if not registro.get(
            "significado"
        ):

            advertencias.append(
                f"Código {codigo}: "
                "significado vacío."
            )

    contador = Counter(
        encontrados
    )

    for codigo, cantidad in (
        contador.items()
    ):

        if cantidad > 1:

            errores.append(
                f"Código duplicado: "
                f"{codigo}"
            )


# ==========================================================
# ESTADÍSTICAS
# ==========================================================

def mostrar_estadisticas(
    base
):

    procedimientos = base.get(
        "procedimientos",
        []
    )

    activos = 0
    validados = 0

    dominios = Counter()

    for procedimiento in (
        procedimientos
    ):

        control = procedimiento.get(
            "control",
            {}
        )

        if control.get(
            "activo",
            True
        ):
            activos += 1

        if control.get(
            "validado",
            False
        ):
            validados += 1

        dominio = procedimiento.get(
            "dominio",
            "sin dominio"
        )

        dominios[dominio] += 1

    print()
    print("=" * 60)
    print("ESTADÍSTICAS")
    print("=" * 60)

    print(
        f"Procedimientos totales: "
        f"{len(procedimientos)}"
    )

    print(
        f"Procedimientos activos: "
        f"{activos}"
    )

    print(
        f"Procedimientos validados: "
        f"{validados}"
    )

    print(
        "Códigos de mantenimiento: "
        f"{len(base.get('codigos_mantenimiento', []))}"
    )

    print(
        "\nProcedimientos por dominio:"
    )

    for dominio, cantidad in (
        dominios.items()
    ):

        print(
            f"- {dominio}: "
            f"{cantidad}"
        )


# ==========================================================
# VALIDACIÓN COMPLETA
# ==========================================================

def validar_base():

    base = cargar_base()

    if base is None:
        return

    errores = []
    advertencias = []

    validar_metadata(
        base,
        errores,
        advertencias
    )

    procedimientos = base.get(
        "procedimientos",
        []
    )

    if not isinstance(
        procedimientos,
        list
    ):

        errores.append(
            "'procedimientos' "
            "debe ser una lista."
        )

        procedimientos = []

    validar_ids(
        procedimientos,
        errores
    )

    for indice, procedimiento in enumerate(
        procedimientos,
        start=1
    ):

        validar_procedimiento(
            procedimiento,
            indice,
            errores,
            advertencias
        )

    validar_codigos(
        base,
        errores,
        advertencias
    )

    print()
    print("=" * 60)
    print(
        "VALIDACIÓN DE BASE DE CONOCIMIENTO"
    )
    print("=" * 60)

    if errores:

        print(
            f"\nERRORES: "
            f"{len(errores)}"
        )

        for error in errores:

            print(
                f"❌ {error}"
            )

    else:

        print(
            "\n✅ No se encontraron "
            "errores estructurales."
        )

    if advertencias:

        print(
            f"\nADVERTENCIAS: "
            f"{len(advertencias)}"
        )

        for advertencia in (
            advertencias
        ):

            print(
                f"⚠️ {advertencia}"
            )

    else:

        print(
            "\n✅ No hay advertencias."
        )

    mostrar_estadisticas(
        base
    )

    print()
    print("=" * 60)

    if errores:

        print(
            "RESULTADO: "
            "BASE CON ERRORES"
        )

    else:

        print(
            "RESULTADO: "
            "BASE ESTRUCTURALMENTE VÁLIDA"
        )

    print("=" * 60)


# ==========================================================
# INICIO
# ==========================================================

if __name__ == "__main__":

    validar_base()