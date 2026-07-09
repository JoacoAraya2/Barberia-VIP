import pywhatkit
import datetime
import time
import os
from dotenv import load_dotenv

load_dotenv()

class WhatsAppManager:
    def __init__(self):
        # Tiempo de espera para que cargue WhatsApp Web (ajustar según tu internet)
        self.wait_time = 15 
        print("📱 WhatsApp Manager iniciado (Modo Web Automático)")

    def send_message(self, phone_number, message):
        """
        Envía un mensaje abriendo WhatsApp Web en el navegador.
        phone_number: Debe incluir el código de país (ej: '52155555555')
        message: Texto a enviar
        """
        try:
            # Limpiar número de símbolos +
            clean_number = phone_number.replace('+', '')
            
            print(f"⏳ Enviando mensaje a {clean_number}... (Se abrirá el navegador)")
            
            # Envía el mensaje inmediatamente (wait_time segundos para cargar web)
            # close_time=3 cierra la pestaña después de enviar
            pywhatkit.sendwhatmsg_instantly(
                phone_no=clean_number,
                message=message,
                wait_time=self.wait_time,
                tab_close=True,
                close_time=3
            )
            print("✅ Mensaje enviado correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error enviando WhatsApp: {e}")
            print("💡 Consejo: Asegúrate de tener sesión iniciada en WhatsApp Web en tu navegador predeterminado.")
            return False

    def get_status(self):
        return {"state": "connected_via_browser", "note": "Requiere navegador abierto"}