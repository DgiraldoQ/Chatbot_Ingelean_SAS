import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from langchain.chat_models import ChatOpenAI
from textblob import TextBlob
import joblib
import pandas as pd

# Cargar variables de entorno
load_dotenv()
OPENAI_API_KEY = os.getenv("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")
TELEGRAM_TOKEN = os.getenv("8009953518:AAFzmjQby5IJFuTL1RL_44kDKH2Blv2mNTQ")

# Cargar modelo entrenado
modelo = joblib.load("modelo.pkl")

# Cargar columnas de entrenamiento para codificación
df = pd.read_csv(r"C:\Users\diego\OneDrive\Documentos\Expo\Documentos despues de la limpieza\proyecto_normalizado.csv", delimiter=";")
df.columns = df.columns.str.strip()
X_base = pd.get_dummies(df.drop("Drug", axis=1))
columnas_modelo = X_base.columns

# Cargar modelo de lenguaje
llm = ChatOpenAI(api_key=OPENAI_API_KEY)

# Función de análisis de sentimientos
def analizar_sentimiento(texto):
    sentimiento = TextBlob(texto).sentiment.polarity
    if sentimiento > 0:
        return "positivo"
    elif sentimiento < 0:
        return "negativo"
    else:
        return "neutral"

# Predicción de medicamento (si usuario da datos tipo formulario)
def predecir_medicamento(datos_usuario: str):
    try:
        partes = datos_usuario.split(",")
        if len(partes) != 5:
            return "Por favor, ingresa los datos como: edad,sexo,BP,colesterol,Na_to_K"

        edad, sexo, bp, col, na_k = partes
        entrada = pd.DataFrame([{
            "Age": int(edad),
            "Sex": sexo.strip(),
            "BP": bp.strip(),
            "Cholesterol": col.strip(),
            "Na_to_K": float(na_k)
        }])

        entrada_codificada = pd.get_dummies(entrada)
        entrada_codificada = entrada_codificada.reindex(columns=columnas_modelo, fill_value=0)

        prediccion = modelo.predict(entrada_codificada)[0]
        return f"🔍 Según los datos ingresados, el medicamento recomendado es: **{prediccion}**"
    except Exception as e:
        return f"❌ Error al procesar: {str(e)}"

# Función para manejar mensajes
async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = update.message.text
    sentimiento = analizar_sentimiento(mensaje)
    if "," in mensaje and mensaje.count(",") == 4:
        respuesta = predecir_medicamento(mensaje)
    else:
        respuesta_llm = llm.predict(f"El usuario dice: {mensaje}. Responde de forma clara y útil.")
        respuesta = f"🤖 Respuesta IA: {respuesta_llm}"

    await update.message.reply_text(f"🧠 Sentimiento: {sentimiento}\n\n{respuesta}")

# Comando de inicio
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola, soy tu asistente médico 🤖. Puedes preguntarme cosas o ingresar datos así: edad,sexo,BP,colesterol,Na_to_K")

# Main para lanzar el bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    print("✅ Bot funcionando...")
    app.run_polling()
