import requests
import os
from dotenv import load_dotenv

load_dotenv()

class WhatsAppManager:
    def __init__(self):
        self.base_url = os.getenv('EVOLUTION_API_URL')
        self.api_key = os.getenv('EVOLUTION_API_KEY')
        self.instance = os.getenv('EVOLUTION_INSTANCE_NAME')
        self.headers = {"apikey": self.api_key, "Content-Type": "application/json"}

    def send_message(self, phone_number, message):
        # Asegurar formato número (sin +)
        clean_number = phone_number.replace('+', '').split('@')[0]
        
        url = f"{self.base_url}/message/sendText/{self.instance}"
        payload = {
            "number": clean_number,
            "textMessage": {"text": message}
        }
        
        try:
            resp = requests.post(url, json=payload, headers=self.headers)
            return resp.status_code == 200
        except Exception as e:
            print(f"Error enviando WhatsApp: {e}")
            return False

    def get_status(self):
        url = f"{self.base_url}/instance/connectionState/{self.instance}"
        try:
            resp = requests.get(url, headers=self.headers)
            return resp.json()
        except:
            return {"state": "disconnected"}