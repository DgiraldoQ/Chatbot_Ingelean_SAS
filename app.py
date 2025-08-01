import os
import pandas as pd
import joblib
from fastapi import FastAPI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from textblob import TextBlob
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Cargar modelo de árboles de decisión
modelo = joblib.load("modelo_entrenado.pkl")  # Este archivo debe estar en la raíz o subido al repo

# Cargar el dataset limpio
data = pd.read_csv("proyecto_normalizado.csv")

# Crear FastAPI app (opcional si solo usarás Telegram, pero necesario para Render)
app = FastAPI()

# Función de predicción a partir del texto
def clasificar_texto(texto):
    sentimiento = TextBlob(texto).sentiment.polarity
    prediccion = modelo.predict([[sentimiento]])[0]
    return f"🔎 Sentimiento: {'positivo' if sentimiento > 0 else 'negativo' if sentimiento < 0 else 'neutral'}\n📊 Clasificación: {prediccion}"

# Comando de bienvenida
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 ¡Hola! Soy tu chatbot. Envíame un mensaje y te diré su clasificación.")

# Manejar mensajes de texto
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    resultado = clasificar_texto(user_input)
    await update.message.reply_text(resultado)

# Token de Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Iniciar el bot con FastAPI (Render ejecutará esto al iniciar)
@app.on_event("startup")
async def startup_event():
    app_bot = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await app_bot.initialize()
    await app_bot.start()
    print("✅ Bot de Telegram iniciado")

@app.get("/")
async def root():
    return {"message": "🚀 Chatbot funcionando correctamente en FastAPI"}
