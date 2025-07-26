from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# Cargar preguntas frecuentes
try:
    faqs_df = pd.read_pickle("faqs_ingelean.pkl")
except Exception as e:
    raise RuntimeError(f"Error al cargar faqs_ingelean.pkl: {e}")

# Diccionario temporal de usuarios
usuarios = {}

@app.route("/responder", methods=["POST"])
def responder():
    data = request.get_json()

    # Validación inicial
    if not data or "pregunta" not in data or "usuario_id" not in data:
        return jsonify({"error": "Faltan los campos 'pregunta' o 'usuario_id'"}), 400

    pregunta_usuario = data["pregunta"].strip().lower()
    usuario_id = str(data["usuario_id"])

    # Paso 1: Solicitar ciudad si no está registrada
    if usuario_id not in usuarios or "ciudad" not in usuarios[usuario_id]:
        ciudades_validas = ["bogotá", "medellín", "pereira", "cali", "manizales", "españa", "paraguay"]
        ciudad_detectada = next((ciudad for ciudad in ciudades_validas if ciudad in pregunta_usuario), None)

        if ciudad_detectada:
            usuarios[usuario_id] = {"ciudad": ciudad_detectada.title()}
        else:
            return jsonify({
                "respuesta": "👋 ¡Hola! Antes de continuar, ¿podrías decirme en qué ciudad te encuentras? (Ej: Medellín, Bogotá, Cali...)",
                "categoria": "Ubicación"
            }), 200

    ciudad = usuarios[usuario_id]["ciudad"]
    preguntas_lista = sorted(set(faqs_df["pregunta"].tolist()))

    def generar_menu():
        mensaje = "🤖 Estas son algunas preguntas frecuentes que puedes hacer:\n\n"
        for i, q in enumerate(preguntas_lista[:10], 1):
            mensaje += f"{i}. {q}\n"
        mensaje += "\n✅ Escribe el número de la opción, tu pregunta directamente, o responde 'otra' si tu duda es distinta."
        return mensaje

    # Paso 2: Si el usuario saluda o pide ayuda
    if pregunta_usuario in {"hola", "menú", "ayuda", "inicio", "opciones", "preguntas", "pregunta", "frecuentes"}:
        return jsonify({
            "respuesta": generar_menu(),
            "categoria": "Menú",
            "ciudad": ciudad
        }), 200

    # Paso 3: Si el usuario responde con número
    if pregunta_usuario.isdigit():
        index = int(pregunta_usuario) - 1
        if 0 <= index < len(preguntas_lista[:10]):
            q_match = preguntas_lista[index]
            row = faqs_df[faqs_df["pregunta"] == q_match].iloc[0]
            return jsonify({
                "pregunta": row.get("pregunta", ""),
                "respuesta": row.get("respuesta", ""),
                "categoria": row.get("categoria", "General"),
                "ciudad": ciudad
            }), 200
        else:
            return jsonify({
                "respuesta": "⚠️ Opción inválida. Por favor selecciona un número del 1 al 10.",
                "categoria": "Error",
                "ciudad": ciudad
            }), 200

    # Paso 4: Coincidencia exacta
    for _, row in faqs_df.iterrows():
        if pregunta_usuario == row["pregunta"].strip().lower():
            return jsonify({
                "pregunta": row.get("pregunta", ""),
                "respuesta": row.get("respuesta", ""),
                "categoria": row.get("categoria", "General"),
                "ciudad": ciudad
            }), 200

    # Paso 5: Coincidencia parcial
    for _, row in faqs_df.iterrows():
        if pregunta_usuario in row["pregunta"].lower():
            return jsonify({
                "pregunta": row.get("pregunta", ""),
                "respuesta": row.get("respuesta", ""),
                "categoria": row.get("categoria", "General"),
                "ciudad": ciudad
            }), 200

    # Paso 6: Similitud por palabras clave
    palabras = set(pregunta_usuario.split())
    for _, row in faqs_df.iterrows():
        pregunta_base = row["pregunta"].lower()
        if any(p in pregunta_base for p in palabras):
            return jsonify({
                "pregunta": row.get("pregunta", ""),
                "respuesta": row.get("respuesta", ""),
                "categoria": row.get("categoria", "General"),
                "ciudad": ciudad
            }), 200

    # Paso 7: Si el usuario dice "otra" o "no"
    if "otra" in pregunta_usuario or "no" in pregunta_usuario:
        return jsonify({
            "respuesta": "📩 Gracias por tu interés. Para casos más específicos, puedes contactarnos en https://ingelean.com o escribir a comercial@ingelean.com",
            "categoria": "Contacto",
            "ciudad": ciudad
        }), 200

    # Paso 8: No hubo coincidencia → mostrar menú
    return jsonify({
        "respuesta": "⚠️ No encontré una coincidencia clara para tu pregunta. Aquí tienes algunas opciones para ayudarte:\n\n" + generar_menu(),
        "categoria": "Sugerencias",
        "ciudad": ciudad
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
