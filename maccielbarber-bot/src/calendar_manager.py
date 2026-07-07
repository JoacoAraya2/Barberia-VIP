"""
Gestor de Google Calendar para MaccielBarber
Maneja la conexión con Google Calendar API para verificar disponibilidad y crear eventos
"""

import os
import json
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pytz

class CalendarManager:
    def __init__(self, credentials_file, calendar_id, timezone='America/Argentina/Buenos_Aires'):
        """
        Inicializa el gestor de calendario
        
        Args:
            credentials_file: Ruta al archivo de credenciales de servicio de Google
            calendar_id: ID del calendario de Google
            timezone: Zona horaria local
        """
        self.credentials_file = credentials_file
        self.calendar_id = calendar_id
        self.timezone = pytz.timezone(timezone)
        self.service = self._authenticate()
    
    def _authenticate(self):
        """Autentica con Google Calendar API usando Service Account"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            return build('calendar', 'v3', credentials=credentials)
        except Exception as e:
            print(f"Error de autenticación: {e}")
            return None
    
    def check_availability(self, date_str, start_hour=9, end_hour=20, duration_minutes=30):
        """
        Verifica disponibilidad para una fecha específica
        
        Args:
            date_str: Fecha en formato 'YYYY-MM-DD'
            start_hour: Hora de inicio de atención (9 = 9:00 AM)
            end_hour: Hora de fin de atención (20 = 8:00 PM)
            duration_minutes: Duración de cada turno en minutos
            
        Returns:
            Lista de horas disponibles
        """
        if not self.service:
            return []
        
        # Convertir fecha a rango de tiempo
        start_date = self.timezone.localize(datetime.strptime(date_str, '%Y-%m-%d'))
        end_date = start_date + timedelta(days=1)
        
        # Obtener eventos del día
        events_result = self.service.events().list(
            calendarId=self.calendar_id,
            timeMin=start_date.isoformat(),
            timeMax=end_date.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Generar todos los turnos posibles
        available_slots = []
        current_time = start_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        end_time = start_date.replace(hour=end_hour, minute=0, second=0, microsecond=0)
        
        while current_time < end_time:
            slot_end = current_time + timedelta(minutes=duration_minutes)
            
            # Verificar si hay conflicto con algún evento
            is_available = True
            for event in events:
                event_start = datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date')).replace('Z', '+00:00'))
                event_start = event_start.astimezone(self.timezone)
                
                event_end = datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date')).replace('Z', '+00:00'))
                event_end = event_end.astimezone(self.timezone)
                
                # Verificar solapamiento
                if current_time < event_end and slot_end > event_start:
                    is_available = False
                    break
            
            if is_available:
                available_slots.append(current_time.strftime('%H:%M'))
            
            current_time = slot_end
        
        return available_slots
    
    def create_pending_booking(self, client_name, service, date_str, time_str, duration_minutes=30):
        """
        Crea un evento pendiente de aprobación
        
        Args:
            client_name: Nombre del cliente
            service: Tipo de servicio (Corte, Barba, Combo)
            date_str: Fecha en formato 'YYYY-MM-DD'
            time_str: Hora en formato 'HH:MM'
            duration_minutes: Duración del servicio
            
        Returns:
            ID del evento creado o None si hubo error
        """
        if not self.service:
            return None
        
        # Crear datetime completo
        start_datetime = self.timezone.localize(
            datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
        )
        end_datetime = start_datetime + timedelta(minutes=duration_minutes)
        
        # Crear evento con estado PENDIENTE
        event = {
            'summary': f'🔴 PENDIENTE: {client_name} - {service}',
            'description': f'Cliente: {client_name}\nServicio: {service}\nEstado: Pendiente de aprobación del barbero',
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': str(self.timezone),
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': str(self.timezone),
            },
            'status': 'tentative',
            'colorId': '11',  # Color rojo/gris para pendiente
        }
        
        try:
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            print(f"Evento pendiente creado: {created_event['id']}")
            return created_event['id']
        except Exception as e:
            print(f"Error creando evento: {e}")
            return None
    
    def confirm_booking(self, event_id):
        """
        Cambia el estado de un evento de PENDIENTE a CONFIRMADO
        
        Args:
            event_id: ID del evento a confirmar
            
        Returns:
            True si se confirmó correctamente, False en caso contrario
        """
        if not self.service:
            return False
        
        try:
            # Obtener evento actual
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            # Modificar título y estado
            old_summary = event['summary']
            new_summary = old_summary.replace('🔴 PENDIENTE:', '✅ CONFIRMADO:')
            
            event['summary'] = new_summary
            event['status'] = 'confirmed'
            event['colorId'] = '10'  # Color verde para confirmado
            
            # Actualizar evento
            updated_event = self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            
            print(f"Evento confirmado: {updated_event['id']}")
            return True
        except Exception as e:
            print(f"Error confirmando evento: {e}")
            return False
    
    def cancel_booking(self, event_id):
        """
        Cancela/elimina un evento
        
        Args:
            event_id: ID del evento a cancelar
            
        Returns:
            True si se canceló correctamente, False en caso contrario
        """
        if not self.service:
            return False
        
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            print(f"Evento cancelado: {event_id}")
            return True
        except Exception as e:
            print(f"Error cancelando evento: {e}")
            return False
    
    def get_current_status(self):
        """
        Verifica si el barbero está ocupado en este momento
        
        Returns:
            Dict con estado actual y próximo evento si existe
        """
        if not self.service:
            return {'busy': False, 'current_event': None, 'next_event': None}
        
        now = datetime.now(self.timezone)
        
        # Buscar eventos alrededor de la hora actual
        events_result = self.service.events().list(
            calendarId=self.calendar_id,
            timeMin=now.isoformat(),
            maxResults=2,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return {'busy': False, 'current_event': None, 'next_event': None}
        
        # Verificar primer evento
        first_event = events[0]
        event_start = datetime.fromisoformat(first_event['start'].get('dateTime', first_event['start'].get('date')).replace('Z', '+00:00'))
        event_start = event_start.astimezone(self.timezone)
        
        event_end = datetime.fromisoformat(first_event['end'].get('dateTime', first_event['end'].get('date')).replace('Z', '+00:00'))
        event_end = event_end.astimezone(self.timezone)
        
        # Si el evento ya empezó pero no terminó, está ocupado
        if event_start <= now < event_end:
            return {
                'busy': True,
                'current_event': {
                    'summary': first_event.get('summary', ''),
                    'start': event_start.strftime('%H:%M'),
                    'end': event_end.strftime('%H:%M')
                },
                'next_event': None
            }
        
        # Si hay un próximo evento
        if len(events) > 1:
            next_event = events[1]
            next_start = datetime.fromisoformat(next_event['start'].get('dateTime', next_event['start'].get('date')).replace('Z', '+00:00'))
            next_start = next_start.astimezone(self.timezone)
            
            return {
                'busy': False,
                'current_event': None,
                'next_event': {
                    'summary': next_event.get('summary', ''),
                    'start': next_start.strftime('%H:%M')
                }
            }
        
        return {'busy': False, 'current_event': None, 'next_event': None}
