import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
import paho.mqtt.client as paho
import json
import random

# Configuración WebSockets (Evita bloqueos de firewall en la web)
broker = "broker.emqx.io"
port = 8083 # Puerto para WebSockets
TOPIC_CONTROL = "proyecto/deshumidificador/control"
TOPIC_HUMEDAD = "proyecto/deshumidificador/humedad"

# Variables de sesión
if "humedad" not in st.session_state:
    st.session_state.humedad = "--"

# Función de recepción de datos MQTT
def on_message(client, userdata, msg):
    try:
        if msg.topic == TOPIC_HUMEDAD:
            st.session_state.humedad = msg.payload.decode()
    except Exception as e:
        pass

# Inicialización segura del cliente MQTT para Web
@st.cache_resource
def init_mqtt():
    # ID aleatorio para evitar colisiones
    client_id = f"Streamlit_UI_{random.randint(1000, 9999)}"
    # Transport=websockets es obligatorio para el puerto 8083
    client = paho.Client(client_id, transport="websockets")
    client.on_message = on_message
    try:
        client.connect(broker, port)
        client.subscribe(TOPIC_HUMEDAD)
        client.loop_start() # Hilo en segundo plano
    except Exception as e:
        st.error(f"Error de red: {e}")
    return client

client1 = init_mqtt()

# ---------------- INTERFAZ GRÁFICA ----------------

st.title("🌬️ Control - Deshumidificador IoT")

st.subheader("📡 Monitoreo en Tiempo Real")
col1, col2 = st.columns(2)
with col1:
    st.metric(label="Humedad Actual", value=f"{st.session_state.humedad} %")
with col2:
    st.write("")
    st.write("")
    # Este botón fuerza a Streamlit a redibujar la pantalla con el nuevo dato
    if st.button("🔄 Actualizar Lectura de Interfaz"):
        st.rerun()

st.markdown("---")

st.subheader("🎙️ Control por Comandos Hablados")
st.write("Comandos soportados: *'Enciende el deshumidificador'*, *'Apaga el deshumidificador'*")

# Botón de Voz (JS)
stt_button = Button(label="▶️ Iniciar reconocimiento", width=250)
stt_button.js_on_event("button_click", CustomJS(code="""
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'es-ES';
 
    recognition.onresult = function (e) {
        var value = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
        }
        if (value != "") {
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
        }
    }
    recognition.start();
"""))

result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0
)

# Procesamiento de Voz
if result and "GET_TEXT" in result:
    texto_reconocido = result.get("GET_TEXT")
    st.success(f"🗣️ Texto reconocido: {texto_reconocido}")
    
    texto_min = texto_reconocido.lower()
    comando_detectado = None

    if "enciende" in texto_min or "prende" in texto_min:
        if "deshumidificador" in texto_min or "sistema" in texto_min:
            comando_detectado = "ON"
    elif "apaga" in texto_min or "detén" in texto_min:
        if "deshumidificador" in texto_min or "sistema" in texto_min:
            comando_detectado = "OFF"

    if comando_detectado:
        try:
            payload = json.dumps({"relay": comando_detectado})
            client1.publish(TOPIC_CONTROL, payload)
            st.info(f"📡 Comando enviado al simulador: {comando_detectado}")
        except Exception as e:
            st.error(f"❌ Error enviando comando: {e}")
    else:
        st.warning("⚠️ Comando no válido. Debes decir 'Enciende el deshumidificador'.")
