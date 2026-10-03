from motor_busqueda import (
    cargar_base,
    consultar
)


# ==========================================================
# PREGUNTAS DE PRUEBA
# ==========================================================

PREGUNTAS_PRUEBA = [

    "¿Cómo reprogramo una SOT?",

    "El cliente quiere cambiar la fecha de la visita",

    "No hay cuadrillas y tengo que cambiar la fecha",

    "El técnico llegó tarde y el cliente ya no puede atenderlo",

    "¿Cuáles son las franjas de atención?",

    "¿Puedo programar al cliente a las 7 de la mañana?",

    "¿Cuál es la dilación máxima de una SOT?",

    "¿Dónde reviso los servicios activos del cliente?",

    "¿Cómo reviso los niveles de FTTH?",

    "Necesito validar la señal de una instalación HFC"
]


# ==========================================================
# PRUEBAS
# ==========================================================

def ejecutar_pruebas():

    base = cargar_base()

    print()
    print("=" * 80)
    print(
        "PRUEBAS DEL MOTOR "
        "DE BÚSQUEDA"
    )
    print("=" * 80)

    for numero, pregunta in enumerate(
        PREGUNTAS_PRUEBA,
        start=1
    ):

        resultado = consultar(
            pregunta,
            base
        )

        print()
        print("=" * 80)

        print(
            f"PRUEBA {numero}"
        )

        print(
            f"Pregunta: "
            f"{pregunta}"
        )

        print("-" * 80)

        if (
            resultado[
                "tipo"
            ]
            ==
            "procedimiento"
        ):

            procedimiento = (
                resultado[
                    "procedimiento"
                ]
            )

            print(
                "Resultado:",
                procedimiento[
                    "id"
                ],
                "-",
                procedimiento[
                    "titulo"
                ]
            )

            print(
                "Puntuación:",
                resultado[
                    "puntuacion"
                ]
            )

        else:

            print(
                "Resultado:",
                resultado[
                    "tipo"
                ]
            )

        print()
        print(
            resultado[
                "respuesta"
            ]
        )


# ==========================================================
# INICIO
# ==========================================================

if __name__ == "__main__":

    ejecutar_pruebas()