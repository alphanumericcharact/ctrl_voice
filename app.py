import os
import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
import time
import glob
import paho.mqtt.client as paho
import json
from gtts import gTTS
from googletrans import Translator

def on_publish(client,userdata,result):
    print("el dato ha sido publicado \n")
    pass

def on_message(client, userdata, message):
    global message_received
    time.sleep(2)
    message_received=str(message.payload.decode("utf-8"))
    st.write("📩 Respuesta del sistema:", message_received)

broker="broker.mqttdashboard.com"
port=1883

client1= paho.Client("LKJUHASL")
client1.on_message = on_message

# 🎯 NUEVA INTERFAZ

st.title("🧠 Aplicación Didáctica de Interacción por Voz")

st.subheader("🎙️ Control inteligente mediante comandos hablados")

st.write("""
Esta aplicación permite explorar la interacción entre humanos y sistemas digitales
a través del reconocimiento de voz.

El sistema captura comandos hablados en lenguaje natural y los envía a un dispositivo
externo mediante el protocolo MQTT, permitiendo ejecutar acciones en tiempo real.

### 📌 Instrucciones de uso:
1. Presiona el botón **Inicio**.
2. Habla claramente uno de los comandos.
3. Observa cómo el sistema interpreta y envía la instrucción.

### 🗣️ Ejemplos de comandos:
- "enciende las luces"
- "apaga las luces"
- "abre la puerta"
- "cierra la puerta"
""")

st.info("💡 Asegúrate de permitir el acceso al micrófono en tu navegador.")

st.write("### 🎤 Activar reconocimiento de voz")

stt_button = Button(label="▶️ Iniciar reconocimiento", width=250)

stt_button.js_on_event("button_click", CustomJS(code="""
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
 
    recognition.onresult = function (e) {
        var value = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
        }
        if ( value != "") {
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

# 📡 PROCESAMIENTO DEL TEXTO

if result:
    if "GET_TEXT" in result:
        texto = result.get("GET_TEXT")
        
        st.success(f"🗣️ Comando reconocido: {texto}")

        client1.on_publish = on_publish                            
        client1.connect(broker,port)  

        message = json.dumps({"Act1": texto.strip()})
        ret = client1.publish("voice_ctrl", message)

    try:
        os.mkdir("temp")
    except:
        pass
