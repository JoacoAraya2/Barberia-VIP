"""
Integración con Evolution API para WhatsApp
Maneja el envío y recepción de mensajes de WhatsApp
"""

import requests
import json
from datetime import datetime

class WhatsAppManager:
    def __init__(self, api_url, instance_name, api_key):
        """
        Inicializa el gestor de WhatsApp
        
        Args:
            api_url: URL base de Evolution API (ej: http://localhost:8080)
            instance_name: Nombre de la instancia configurada en Evolution
            api_key: API Key de autenticación
        """
        self.api_url = api_url.rstrip('/')
        self.instance_name = instance_name
        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'apikey': api_key
        }
    
    def send_message(self, phone_number, message):
        """
        Envía un mensaje de texto a un número de WhatsApp
        
        Args:
            phone_number: Número de teléfono (con código de país, ej: 5491112345678)
            message: Mensaje a enviar
            
        Returns:
            True si se envió correctamente, False en caso contrario
        """
        endpoint = f"{self.api_url}/message/sendText/{self.instance_name}"
        
        payload = {
            "number": phone_number,
            "textMessage": {
                "text": message
            }
        }
        
        try:
            response = requests.post(endpoint, json=payload, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Mensaje enviado a {phone_number}")
                return True
            else:
                print(f"❌ Error enviando mensaje: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Excepción enviando mensaje: {e}")
            return False
    
    def send_approval_request_to_barber(self, barber_phone, client_name, service, date, time, event_id):
        """
        Envía solicitud de aprobación al barbero
        
        Args:
            barber_phone: Número del barbero
            client_name: Nombre del cliente
            service: Servicio solicitado
            date: Fecha solicitada
            time: Hora solicitada
            event_id: ID del evento en Google Calendar
            
        Returns:
            True si se envió correctamente
        """
        message = (
            f"💈 *Nueva solicitud en MaccielBarber*\n\n"
            f"👤 Cliente: {client_name}\n"
            f"✂️ Servicio: {service}\n"
            f"📅 Fecha: {date}\n"
            f"⏰ Hora: {time}\n"
            f"🆔 ID Evento: {event_id}\n\n"
            f"*Respondé:* \n"
            f"1️⃣ para APROBAR\n"
            f"2️⃣ para RECHAZAR"
        )
        
        return self.send_message(barber_phone, message)
    
    def send_confirmation_to_client(self, client_phone, client_name, service, date, time):
        """
        Envía confirmación de cita al cliente
        
        Args:
            client_phone: Número del cliente
            client_name: Nombre del cliente
            service: Servicio reservado
            date: Fecha confirmada
            time: Hora confirmada
            
        Returns:
            True si se envió correctamente
        """
        message = (
            f"✅ *¡Tu cita ha sido CONFIRMADA!*\n\n"
            f"Te esperamos en MaccielBarber 💈\n\n"
            f"👤 Cliente: {client_name}\n"
            f"✂️ Servicio: {service}\n"
            f"📅 Fecha: {date}\n"
            f"⏰ Hora: {time}\n\n"
            f"¡Llegá puntual! Si necesitás cancelar o reprogramar, avisá con anticipación. ✂️"
        )
        
        return self.send_message(client_phone, message)
    
    def send_rejection_to_client(self, client_phone, client_name, service, date, time):
        """
        Informa al cliente que su cita fue rechazada
        
        Args:
            client_phone: Número del cliente
            client_name: Nombre del cliente
            service: Servicio solicitado
            date: Fecha solicitada
            time: Hora solicitada
            
        Returns:
            True si se envió correctamente
        """
        message = (
            f"❌ *Lo sentimos, {client_name}*\n\n"
            f"El barbero no puede atenderte en el horario solicitado:\n"
            f"📅 {date} a las {time}\n"
            f"✂️ Servicio: {service}\n\n"
            f"Fue por un imprevisto de última hora. ¿Te gustaría ver otros horarios disponibles? "
            f"Respondé 'horarios' para ver opciones. 💈"
        )
        
        return self.send_message(client_phone, message)
    
    def check_instance_status(self):
        """
        Verifica el estado de la instancia de WhatsApp
        
        Returns:
            Dict con el estado de la instancia
        """
        endpoint = f"{self.api_url}/instance/connectionState/{self.instance_name}"
        
        try:
            response = requests.get(endpoint, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error verificando estado: {response.status_code}")
                return {'status': 'error'}
        except Exception as e:
            print(f"Excepción verificando estado: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_qr_code(self):
        """
        Obtiene el código QR para vincular WhatsApp
        
        Returns:
            URL o datos del QR, o None si hay error
        """
        endpoint = f"{self.api_url}/instance/fetchInstance/{self.instance_name}"
        
        try:
            response = requests.get(endpoint, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error obteniendo QR: {response.status_code}")
                return None
        except Exception as e:
            print(f"Excepción obteniendo QR: {e}")
            return None
