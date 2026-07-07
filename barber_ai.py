import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

class BarberAI:
    def __init__(self):
        self.url = os.getenv('AI_MODEL_URL', 'http://localhost:11434/api/generate')
        self.model = os.getenv('AI_MODEL_NAME', 'qwen2.5:7b')
        
        self.system_prompt = """
        Eres el asistente virtual de "MaccielBarber". Tono profesional, urbano y amable.
        OBJETIVOS:
        1. Agendar citas solo tras verificar disponibilidad.
        2. NUNCA confirmar sin aprobación. Cita = "PENDIENTE".
        3. Servicios: Corte ($10), Barba ($5), Combo ($14).
        
        FLUJO:
        1. Saluda y pregunta nombre/servicio/hora.
        2. Si pide hora, di: "Verificando...". (El sistema externo llamará a check_availability).
        3. Si hay hueco, di: "Hay hueco a las X. ¿Reservo como PENDIENTE?".
        4. Si acepta, indica que se avisará al barbero.
        
        FORMATO DE SALIDA PARA EL SISTEMA:
        Si el usuario quiere agendar, responde con un JSON al final envuelto en triple backticks:
        ```json
        {"action": "check_availability", "date": "YYYY-MM-DD", "time": "HH"}
        ```
        o
        ```json
        {"action": "create_pending", "name": "Juan", "service": "Corte", "date": "...", "time": "..."}
        ```
        Si es charla normal, responde solo texto.
        """

    def generate_response(self, user_message, context=[]):
        messages = [{"role": "system", "content": self.system_prompt}] + context + [{"role": "user", "content": user_message}]
        
        payload = {
            "model": self.model,
            "prompt": "\n".join([f"{m['role']}: {m['content']}" for m in messages]),
            "stream": False
        }
        
        try:
            response = requests.post(self.url, json=payload)
            if response.status_code == 200:
                text = response.json().get('response', '')
                return text
            else:
                return "Lo siento, estoy teniendo problemas de conexión con mi cerebro IA."
        except Exception as e:
            return f"Error de IA: {str(e)}"

    def parse_action(self, text):
        """Extrae acciones JSON del texto de la IA"""
        try:
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
        except:
            pass
        return None