from motor_busqueda import cargar_base, consultar

PRUEBAS = [
    ("AB03", "codigo", "AB03"),
    ("que significa AB03", "codigo", "AB03"),
    ("PC18", "codigo", "PC18"),
    ("qué significa PC21", "codigo", "PC21"),
    ("FI09", "codigo", "FI09"),
    ("ZZ99", "sin_resultado", None),
    ("a", "sin_resultado", None),
    ("hola", "sin_resultado", None),
    ("quiero cocinar arroz", "sin_resultado", None),
    ("como valido niveles FTTH", "procedimiento", None),
    ("donde reviso receiving power FTTH", "procedimiento", None),
    ("el tecnico llego tarde y paso la franja", "procedimiento", None),
]

def ejecutar_pruebas():
    base = cargar_base()
    correctas = 0

    print("=" * 90)
    print("PRUEBAS DEL MOTOR")
    print("=" * 90)

    for i, (pregunta, tipo_esperado, codigo_esperado) in enumerate(PRUEBAS, 1):
        resultado = consultar(pregunta, base)
        tipo_obtenido = resultado.get("tipo")
        codigo_obtenido = (
            resultado.get("codigo", {}).get("codigo")
            if tipo_obtenido == "codigo"
            else None
        )

        ok = (
            tipo_obtenido == tipo_esperado
            and (codigo_esperado is None or codigo_obtenido == codigo_esperado)
        )

        correctas += int(ok)

        print(f"\n{i:02d}. {'OK' if ok else 'REVISAR'}")
        print("Pregunta:", pregunta)
        print("Tipo esperado:", tipo_esperado)
        print("Tipo obtenido:", tipo_obtenido)
        if codigo_esperado:
            print("Código esperado:", codigo_esperado)
            print("Código obtenido:", codigo_obtenido)
        print(resultado.get("respuesta"))

    print("\n" + "=" * 90)
    print(f"Correctas: {correctas}/{len(PRUEBAS)}")
    print(f"Precisión: {correctas / len(PRUEBAS) * 100:.1f}%")

if __name__ == "__main__":
    ejecutar_pruebas()
