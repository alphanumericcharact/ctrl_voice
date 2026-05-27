import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
import paho.mqtt.client as paho
import json

broker = "broker.emqx.io"
port = 1883
TOPIC_CONTROL = "proyecto/deshumidificador/control"
TOPIC_HUMEDAD = "proyecto/deshumidificador/humedad"

# Variables de sesion para almacenar datos en tiempo real
if "humedad" not in st.session_state:
    st.session_state.humedad = "--"

# Funcion que se ejecuta al recibir un mensaje del ESP32
def on_message(client, userdata, msg):
    try:
        if msg.topic == TOPIC_HUMEDAD:
            st.session_state.humedad = msg.payload.decode()
    except Exception as e:
        print(f"Error procesando mensaje: {e}")

# Configuracion del Cliente MQTT en Streamlit
@st.cache_resource
def init_mqtt():
    client = paho.Client("Streamlit_Dashboard_UI")
    client.on_message = on_message
    try:
        client.connect(broker, port)
        client.subscribe(TOPIC_HUMEDAD)
        client.loop_start() # Hilo en segundo plano para escuchar
    except Exception as e:
        st.error(f"Error conectando al broker MQTT: {e}")
    return client

client1 = init_mqtt()

st.title("Control - Deshumidificador IoT")

# Panel de Monitoreo
st.subheader("Monitoreo en Tiempo Real")
col1, col2 = st.columns(2)
with col1:
    st.metric(label="Humedad Actual", value=f"{st.session_state.humedad} %")
with col2:
    if st.button("Actualizar Lectura de Interfaz"):
        st.rerun()

st.markdown("---")

# Interfaz de Control por Voz
st.subheader("Control por Comandos Hablados")
st.write("Comandos soportados: 'Enciende el deshumidificador', 'Apaga el deshumidificador'")

stt_button = Button(label="Iniciar reconocimiento", width=250)
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

# Procesamiento de Voz a MQTT
if result and "GET_TEXT" in result:
    texto_reconocido = result.get("GET_TEXT")
    st.success(f"Texto reconocido: {texto_reconocido}")
    
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
            st.info(f"MQTT Publicado: {payload}")
        except Exception as e:
            st.error(f"Error de conexion MQTT: {e}")
    else:
        st.warning("Comando no ejecutable. Falta palabra clave.")
