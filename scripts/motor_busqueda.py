import json
import re
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO_BD = RAIZ / "data" / "base_conocimiento.json"

UMBRAL_RESPUESTA = 10.0
UMBRAL_ALTA = 20.0
UMBRAL_MEDIA = 14.0
MAX_RESULTADOS = 5

STOPWORDS = {
    "a","al","algo","como","con","cual","cuales","cuando","de","del","donde",
    "el","ella","en","es","esta","este","esto","hacer","hay","la","las","lo",
    "los","me","mi","para","por","que","se","si","su","un","una","y","o"
}

PATRON_CODIGO = re.compile(r"\b[A-Z]{2}\d{2}\b", re.IGNORECASE)

def cargar_base():
    if not ARCHIVO_BD.exists():
        raise FileNotFoundError("No se encontró data/base_conocimiento.json")
    with open(ARCHIVO_BD, "r", encoding="utf-8") as archivo:
        return json.load(archivo)

def normalizar_texto(texto):
    if texto is None:
        return ""
    texto = str(texto).lower()
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()

def tokenizar(texto):
    return [
        p for p in normalizar_texto(texto).split()
        if p not in STOPWORDS and len(p) >= 3
    ]

def extraer_codigos(texto):
    return [x.upper() for x in PATRON_CODIGO.findall(str(texto))]

def buscar_codigo_mantenimiento(pregunta, base):
    codigos_pregunta = extraer_codigos(pregunta)
    if not codigos_pregunta:
        return None

    catalogo = {
        str(r.get("codigo", "")).strip().upper(): r
        for r in base.get("codigos_mantenimiento", [])
        if r.get("control", {}).get("activo", True)
    }

    for codigo in codigos_pregunta:
        if codigo in catalogo:
            return catalogo[codigo]

    return None

def construir_respuesta_codigo(registro):
    codigo = registro.get("codigo", "")
    categoria = registro.get("categoria", "")
    significado = registro.get("significado", "")
    adicional = registro.get("detalle_adicional", "")
    registro_sga = registro.get("registro_sga", "")

    lineas = [
        "CÓDIGO DE MANTENIMIENTO",
        "",
        f"Código: {codigo}",
        f"Categoría: {categoria}",
        f"Significado: {significado}",
    ]

    if adicional:
        lineas.append(f"Detalle adicional: {adicional}")

    if registro_sga:
        lineas += ["", f"Registro SGA: {registro_sga}"]

    return "\n".join(lineas)

def similitud(a, b):
    a, b = normalizar_texto(a), normalizar_texto(b)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()

def textos_busqueda(procedimiento):
    textos = [
        ("titulo", procedimiento.get("titulo", ""), 8.0),
        ("dominio", procedimiento.get("dominio", ""), 2.0)
    ]

    busqueda = procedimiento.get("busqueda", {})
    for x in busqueda.get("consultas_ejemplo", []):
        textos.append(("consulta_ejemplo", x, 7.0))
    for x in busqueda.get("palabras_clave", []):
        textos.append(("palabra_clave", x, 5.0))
    for x in busqueda.get("sinonimos", []):
        textos.append(("sinonimo", x, 5.0))

    clasificacion = procedimiento.get("clasificacion", {})
    for x in clasificacion.get("tipo_sot", []):
        textos.append(("tipo_sot", x, 3.0))
    for x in clasificacion.get("tecnologia", []):
        textos.append(("tecnologia", x, 3.0))
    for x in clasificacion.get("aplicativos", []):
        textos.append(("aplicativo", x, 3.0))

    return textos

def evidencia_lexica(pregunta, procedimiento):
    tokens_p = set(tokenizar(pregunta))
    if len(tokens_p) < 2:
        return False, 0, False

    max_comunes = 0
    frase_fuerte = False
    pregunta_n = normalizar_texto(pregunta)

    for campo, texto, _ in textos_busqueda(procedimiento):
        texto_n = normalizar_texto(texto)
        if not texto_n:
            continue

        tokens_t = set(tokenizar(texto))
        comunes = len(tokens_p & tokens_t)
        max_comunes = max(max_comunes, comunes)

        if (
            len(texto_n) >= 5
            and (texto_n in pregunta_n or pregunta_n in texto_n)
            and campo in {"titulo", "consulta_ejemplo", "palabra_clave", "sinonimo"}
        ):
            frase_fuerte = True

    return (frase_fuerte or max_comunes >= 2), max_comunes, frase_fuerte

def puntuar_procedimiento(pregunta, procedimiento):
    valida, max_comunes, frase_fuerte = evidencia_lexica(pregunta, procedimiento)
    if not valida:
        return 0.0, []

    pregunta_n = normalizar_texto(pregunta)
    tokens_p = set(tokenizar(pregunta))
    puntuacion = 0.0
    razones = []

    for campo, texto, peso in textos_busqueda(procedimiento):
        texto_n = normalizar_texto(texto)
        if not texto_n:
            continue

        tokens_t = set(tokenizar(texto))
        comunes = tokens_p & tokens_t
        puntos = 0.0

        if texto_n == pregunta_n:
            puntos += peso + 8.0
        elif len(texto_n) >= 5 and texto_n in pregunta_n:
            puntos += peso + 5.0
        elif len(pregunta_n) >= 5 and pregunta_n in texto_n:
            puntos += peso * 0.8

        if comunes:
            cobertura = len(comunes) / max(len(tokens_p), 1)
            puntos += cobertura * peso
            if len(comunes) >= 2:
                puntos += min(3.0, len(comunes) * 0.8)

        if comunes or frase_fuerte:
            s = similitud(pregunta, texto)
            if s >= 0.55:
                puntos += s * peso * 0.4

        if puntos > 0:
            puntuacion += puntos
            razones.append({
                "campo": campo,
                "valor": texto,
                "puntos": round(puntos, 2)
            })

    if max_comunes < 2 and not frase_fuerte:
        return 0.0, []

    return round(puntuacion, 2), razones

def construir_respuesta_procedimiento(procedimiento):
    respuesta = procedimiento.get("respuesta", {})
    lineas = [f"PROCEDIMIENTO: {procedimiento.get('titulo', '')}"]

    resumen = respuesta.get("resumen", "")
    if resumen:
        lineas += ["", resumen]

    pasos = respuesta.get("pasos", [])
    if pasos:
        lineas += ["", "PASOS:"]
        for paso in sorted(pasos, key=lambda x: x.get("orden", 0)):
            app = paso.get("aplicativo", "")
            accion = paso.get("accion", "")
            prefijo = f"[{app}] " if app else ""
            lineas.append(f"{paso.get('orden', '')}. {prefijo}{accion}")
            if paso.get("validacion"):
                lineas.append(f"   Verificar: {paso['validacion']}")
            if paso.get("si_no_cumple"):
                lineas.append(f"   Si no cumple: {paso['si_no_cumple']}")

    for titulo, clave in [
        ("PRECONDICIONES", "precondiciones"),
        ("VERIFICAR", "verificaciones"),
        ("ADVERTENCIAS", "advertencias")
    ]:
        elementos = respuesta.get(clave, [])
        if elementos:
            lineas += ["", f"{titulo}:"]
            lineas.extend(f"- {x}" for x in elementos)

    if respuesta.get("accion_si_no_cumple"):
        lineas += ["", "SI NO CUMPLE:", respuesta["accion_si_no_cumple"]]
    if respuesta.get("escalamiento"):
        lineas += ["", "ESCALAMIENTO:", respuesta["escalamiento"]]

    return "\n".join(lineas)

def buscar_procedimientos(pregunta, base):
    resultados = []

    for procedimiento in base.get("procedimientos", []):
        control = procedimiento.get("control", {})
        if not control.get("activo", True):
            continue

        puntuacion, razones = puntuar_procedimiento(pregunta, procedimiento)

        if puntuacion >= UMBRAL_RESPUESTA:
            confianza = (
                "ALTA" if puntuacion >= UMBRAL_ALTA
                else "MEDIA" if puntuacion >= UMBRAL_MEDIA
                else "BAJA"
            )
            resultados.append({
                "procedimiento": procedimiento,
                "puntuacion": puntuacion,
                "confianza": confianza,
                "razones": razones
            })

    resultados.sort(key=lambda x: x["puntuacion"], reverse=True)
    return resultados[:MAX_RESULTADOS]

def consultar(pregunta, base):
    respuesta_sin = base.get("configuracion", {}).get(
        "respuesta_sin_resultado",
        "No existe información confirmada para esta consulta en la base de conocimiento. "
        "Consulta con tu supervisor a cargo."
    )

    # IMPORTANTE: buscar código ANTES de evaluar longitud de la pregunta.
    codigo = buscar_codigo_mantenimiento(pregunta, base)
    if codigo:
        return {
            "tipo": "codigo",
            "confianza": "ALTA",
            "respuesta": construir_respuesta_codigo(codigo),
            "codigo": codigo,
            "resultados": [codigo]
        }

    # Si escribió un código con formato correcto pero no existe en catálogo.
    codigos_escritos = extraer_codigos(pregunta)
    if codigos_escritos:
        return {
            "tipo": "sin_resultado",
            "confianza": "NINGUNA",
            "respuesta": (
                f"El código {codigos_escritos[0]} no existe en el catálogo de mantenimiento registrado. "
                "Consulta con tu supervisor a cargo."
            ),
            "resultados": []
        }

    if len(tokenizar(pregunta)) < 2:
        return {
            "tipo": "sin_resultado",
            "confianza": "NINGUNA",
            "respuesta": respuesta_sin,
            "resultados": []
        }

    resultados = buscar_procedimientos(pregunta, base)

    if not resultados:
        return {
            "tipo": "sin_resultado",
            "confianza": "NINGUNA",
            "respuesta": respuesta_sin,
            "resultados": []
        }

    mejor = resultados[0]

    return {
        "tipo": "procedimiento",
        "confianza": mejor["confianza"],
        "respuesta": construir_respuesta_procedimiento(mejor["procedimiento"]),
        "procedimiento": mejor["procedimiento"],
        "puntuacion": mejor["puntuacion"],
        "razones": mejor["razones"],
        "resultados": resultados
    }

if __name__ == "__main__":
    base = cargar_base()

    print("=" * 70)
    print("MOTOR DE BÚSQUEDA - ASISTENTE TÉCNICO")
    print("=" * 70)
    print("Escribe 'salir' para terminar.")

    while True:
        pregunta = input("\nPregunta: ").strip()

        if normalizar_texto(pregunta) == "salir":
            break

        resultado = consultar(pregunta, base)

        print("\n" + "-" * 70)
        print(resultado["respuesta"])
        print("-" * 70)
        print("Tipo:", resultado["tipo"])
        print("Confianza:", resultado["confianza"])

        if resultado["tipo"] == "procedimiento":
            p = resultado["procedimiento"]
            print("Seleccionado:", p.get("id"), "-", p.get("titulo"))
            print("Puntuación:", resultado["puntuacion"])
