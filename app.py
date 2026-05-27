import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
import paho.mqtt.client as paho
import json

# Configuración MQTT Broker
broker = "broker.mqttdashboard.com"
port = 1883
TOPIC_CONTROL = "proyecto/deshumidificador/control"

def on_publish(client, userdata, result):
    pass

client1 = paho.Client("Streamlit_Voice_Ctrl")
client1.on_publish = on_publish

# Interfaz Web de Streamlit
st.title("🌬️ Control por Voz - Deshumidificador IoT")
st.subheader("🎙️ Módulo de interacción por comandos hablados")

st.write("""
### 📌 Instrucciones de uso:
1. Presiona el botón **Iniciar reconocimiento**.
2. Otorga permisos de micrófono al navegador si se solicitan.
3. Habla claramente diciendo uno de los comandos válidos.

### 🗣️ Comandos Soportados:
* *"Enciende el deshumidificador"* o *"Prende el deshumidificador"*
* *"Apaga el deshumidificador"*
""")

# Componente de reconocimiento de voz usando la API Web Speech del navegador
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

# Procesamiento del comando de voz y envío MQTT
if result and "GET_TEXT" in result:
    texto_reconocido = result.get("GET_TEXT")
    st.success(f"🗣️ Texto reconocido: \"{texto_reconocido}\"")
    
    # Normalizar texto a minúsculas para análisis
    texto_min = texto_reconocido.lower()
    comando_detectado = None

    # Lógica de discriminación de comandos
    if "enciende" in texto_min or "prende" in texto_min:
        if "deshumidificador" in texto_min or "sistema" in texto_min:
            comando_detectado = "ON"
    elif "apaga" in texto_min or "detén" in texto_min:
        if "deshumidificador" in texto_min or "sistema" in texto_min:
            comando_detectado = "OFF"

    # Envío de carga útil al Broker si el comando es válido
    if comando_detectado:
        try:
            client1.connect(broker, port)
            payload = json.dumps({"relay": comando_detectado})
            client1.publish(TOPIC_CONTROL, payload)
            st.info(f"📡 MQTT Publicado $\rightarrow$ `{payload}` en el tópico `{TOPIC_CONTROL}`")
        except Exception as e:
            st.error(f"❌ Error de conexión MQTT: {e}")
    else:
        st.warning("⚠️ Comando no ejecutable. Asegúrate de incluir la palabra 'enciende' o 'apaga' junto a 'deshumidificador'.")
