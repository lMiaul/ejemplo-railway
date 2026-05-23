import streamlit as st
import pymongo
import os
from google import genai

# 1. Configuración de variables de entorno
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# 2. Conexión a MongoDB
@st.cache_resource
def init_connection():
    client = pymongo.MongoClient(MONGO_URL)
    # Se crea/usa la base de datos 'demo_db' y la colección 'feedbacks'
    return client["demo_db"]["feedbacks"]

collection = init_connection()

# 3. Cliente de Gemini
client = genai.Client(api_key=GOOGLE_API_KEY)

# 4. Interfaz de Usuario
st.title("📊 Analizador de Feedback en Tiempo Real")
st.write("Ingresa una reseña. La IA detectará el sentimiento y lo guardaremos en MongoDB.")

feedback_text = st.text_area("Escribe tu reseña aquí:", placeholder="Ej: El servicio fue increíble, me encantó.")

if st.button("Analizar y Guardar"):
    if not feedback_text:
        st.warning("Por favor, ingresa un texto.")
    elif not GOOGLE_API_KEY:
        st.error("Falta la GOOGLE_API_KEY en las variables de entorno.")
    else:
        with st.spinner("Analizando sentimiento..."):
            # Prompt estricto para que la IA responda solo con la categoría
            prompt = f"Analiza el sentimiento del siguiente texto y responde SOLO con una de estas palabras: POSITIVO, NEGATIVO o NEUTRAL. Texto: '{feedback_text}'"
            
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                sentimiento = response.text.strip().upper()
                
                # Guardar en MongoDB
                doc = {"texto": feedback_text, "sentimiento": sentimiento}
                collection.insert_one(doc)
                
                st.success(f"¡Análisis completado! Sentimiento: **{sentimiento}**")
            except Exception as e:
                st.error(f"Error al conectar con la API: {e}")

# 5. Mostrar Historial de la Base de Datos
st.markdown("### 🗄️ Historial en Base de Datos")
# Traemos los últimos 10 registros
historial = list(collection.find({}, {"_id": 0}).limit(10).sort("_id", -1))

if historial:
    st.table(historial)
else:
    st.info("La base de datos está vacía. ¡Analiza tu primer comentario!")
