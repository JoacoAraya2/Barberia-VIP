import os
import json
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

class CalendarManager:
    def __init__(self):
        self.creds_file = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        self.calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
        self.timezone = os.getenv('TIMEZONE', 'UTC')
        self.service = None
        self._authenticate()

    def _authenticate(self):
        try:
            if not os.path.exists(self.creds_file):
                print(f"⚠️ Error: No se encontró el archivo {self.creds_file}")
                return
            
            creds = service_account.Credentials.from_service_account_file(
                self.creds_file, 
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            self.service = build('calendar', 'v3', credentials=creds)
            print("✅ Conectado a Google Calendar")
        except Exception as e:
            print(f"❌ Error de autenticación: {e}")

    def check_availability(self, date_str):
        """Verifica huecos libres para una fecha específica (YYYY-MM-DD)"""
        if not self.service:
            return []
        
        start_dt = f"{date_str}T09:00:00"
        end_dt = f"{date_str}T20:00:00"
        
        try:
            events_result = self.service.events().list(
                calendarId=self.calendar_id, timeMin=start_dt, timeMax=end_dt,
                singleEvents=True, orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            
            # Lógica simple: asumimos cortes de 1 hora. 
            # Esto es una simplificación; en prod se parsean las horas exactas.
            busy_hours = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                hour = start.split('T')[1][:2]
                busy_hours.append(int(hour))
            
            available = [h for h in range(9, 20) if h not in busy_hours]
            return available
        except Exception as e:
            print(f"Error consultando calendario: {e}")
            return []

    def create_pending_booking(self, client_name, service, date, time):
        """Crea evento PENDIENTE"""
        if not self.service:
            return None
        
        start_dt = f"{date}T{time}:00"
        end_dt = f"{date}T{int(time)+1}:00" # Asume 1 hora de duración
        
        event = {
            'summary': f"🔴 PENDIENTE: {client_name} - {service}",
            'description': f"Cliente: {client_name}\nServicio: {service}\nEstado: Pendiente de aprobación del barbero.",
            'start': {'dateTime': start_dt, 'timeZone': self.timezone},
            'end': {'dateTime': end_dt, 'timeZone': self.timezone},
        }
        
        try:
            created_event = self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
            return created_event['id']
        except Exception as e:
            print(f"Error creando evento: {e}")
            return None

    def confirm_booking(self, event_id):
        """Cambia estado a CONFIRMADO"""
        if not self.service: return False
        try:
            event = self.service.events().get(calendarId=self.calendar_id, eventId=event_id).execute()
            summary = event['summary'].replace("🔴 PENDIENTE", "✅ CONFIRMADO")
            event['summary'] = summary
            event['description'] = event['description'].replace("Pendiente", "Confirmado")
            
            self.service.events().patch(calendarId=self.calendar_id, eventId=event_id, body=event).execute()
            return True
        except Exception as e:
            print(f"Error confirmando: {e}")
            return False