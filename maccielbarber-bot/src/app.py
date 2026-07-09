"""
Aplicación Flask principal para MaccielBarber Bot
Recibe webhooks de WhatsApp, procesa con IA y gestiona calendario
"""

import os
import json
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from dotenv import load_dotenv

from src.calendar_manager import CalendarManager
from src.barber_ai import BarberAI
from src.whatsapp_manager import WhatsAppManager

# Cargar variables de entorno
load_dotenv('config/.env')

app = Flask(__name__)

# Inicializar componentes
calendar_manager = None
barber_ai = None
whatsapp_manager = None

# Almacenamiento temporal de solicitudes pendientes (en producción usar base de datos)
pending_requests = {}

def initialize_components():
    """Inicializa todos los componentes del sistema"""
    global calendar_manager, barber_ai, whatsapp_manager
    
    # Configurar gestor de calendario
    credentials_file = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'config/credentials.json')
    calendar_id = os.getenv('GOOGLE_CALENDAR_ID')
    timezone = os.getenv('TIMEZONE', 'America/Argentina/Buenos_Aires')
    
    if calendar_id:
        calendar_manager = CalendarManager(credentials_file, calendar_id, timezone)
        print("✅ Calendar Manager inicializado")
    else:
        print("⚠️ GOOGLE_CALENDAR_ID no configurado")
    
    # Configurar IA
    ai_model = os.getenv('AI_MODEL', 'rule_based')  # 'ollama', 'gemini', o 'rule_based'
    model_name = os.getenv('MODEL_NAME', 'llama2')
    barber_ai = BarberAI(model=ai_model, model_name=model_name)
    print(f"✅ Barber AI inicializado (modelo: {ai_model})")
    
    # Configurar WhatsApp
    evolution_url = os.getenv('EVOLUTION_API_URL', 'http://localhost:8080')
    instance_name = os.getenv('EVOLUTION_INSTANCE_NAME', 'maccielbarber')
    api_key = os.getenv('EVOLUTION_API_KEY')
    
    if api_key:
        whatsapp_manager = WhatsAppManager(evolution_url, instance_name, api_key)
        print("✅ WhatsApp Manager inicializado")
    else:
        print("⚠️ EVOLUTION_API_KEY no configurado")

def parse_date(date_str):
    """Convierte string de fecha a formato YYYY-MM-DD"""
    try:
        # Manejar formatos comunes
        if '/' in date_str:
            parts = date_str.split('/')
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            if year < 100:
                year += 2000
            return f"{year}-{month:02d}-{day:02d}"
        elif '-' in date_str:
            parts = date_str.split('-')
            return f"{parts[2]}-{parts[1]:02d}-{parts[0]:02d}"
        elif date_str.lower() == 'hoy':
            return datetime.now().strftime('%Y-%m-%d')
        elif date_str.lower() == 'mañana':
            return (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            return date_str
    except:
        return None

def parse_time(time_str):
    """Convierte string de hora a formato HH:MM"""
    try:
        # Extraer números del string
        import re
        numbers = re.findall(r'\d+', time_str)
        
        if len(numbers) >= 1:
            hour = int(numbers[0])
            minute = int(numbers[1]) if len(numbers) > 1 else 0
            
            # Manejar AM/PM
            if 'pm' in time_str.lower() or 'p.m.' in time_str.lower():
                if hour < 12:
                    hour += 12
            elif 'am' in time_str.lower() or 'a.m.' in time_str.lower():
                if hour == 12:
                    hour = 0
            
            return f"{hour:02d}:{minute:02d}"
        
        return None
    except:
        return None

@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """
    Webhook para recibir mensajes de WhatsApp desde Evolution API
    """
    try:
        data = request.json
        print(f"📥 Mensaje recibido: {json.dumps(data, indent=2)}")
        
        # Extraer información del mensaje
        # El formato depende de Evolution API, ajustar según versión
        if 'messages' in data:
            message_data = data['messages'][0]
        elif 'message' in data:
            message_data = data['message']
        else:
            message_data = data
        
        phone_number = message_data.get('key', {}).get('remoteJid', '').replace('@s.whatsapp.net', '')
        message_text = message_data.get('message', {}).get('conversation', '')
        
        if not phone_number or not message_text:
            print("⚠️ Mensaje incompleto")
            return jsonify({'status': 'error', 'message': 'Datos incompletos'}), 400
        
        print(f"📱 De: {phone_number} | Mensaje: {message_text}")
        
        # Procesar mensaje con la IA
        context = {}
        
        # Verificar si el cliente pregunta por estado actual
        if any(word in message_text.lower() for word in ['está', 'ocupado', 'libre', 'cortando', 'disponible']):
            if calendar_manager:
                status = calendar_manager.get_current_status()
                context['current_status'] = status
        
        # Generar respuesta
        response_text = barber_ai.process_message(message_text, phone_number, context)
        
        # Verificar si el cliente quiere agendar y tenemos info completa
        booking_info = barber_ai.extract_booking_info(message_text)
        
        if booking_info and calendar_manager and whatsapp_manager:
            # Parsear fecha y hora
            parsed_date = parse_date(booking_info['fecha'])
            parsed_time = parse_time(booking_info['hora'])
            
            if parsed_date and parsed_time:
                # Verificar disponibilidad
                available_hours = calendar_manager.check_availability(parsed_date)
                
                if parsed_time in available_hours:
                    # Crear evento pendiente
                    duration = 30
                    if booking_info['servicio'] == 'Barba':
                        duration = 20
                    elif booking_info['servicio'] == 'Combo':
                        duration = 45
                    
                    event_id = calendar_manager.create_pending_booking(
                        client_name=booking_info['nombre'],
                        service=booking_info['servicio'],
                        date_str=parsed_date,
                        time_str=parsed_time,
                        duration_minutes=duration
                    )
                    
                    if event_id:
                        # Guardar solicitud pendiente
                        pending_requests[event_id] = {
                            'client_phone': phone_number,
                            'client_name': booking_info['nombre'],
                            'service': booking_info['servicio'],
                            'date': parsed_date,
                            'time': parsed_time,
                            'event_id': event_id
                        }
                        
                        # Enviar solicitud de aprobación al barbero
                        barber_phone = os.getenv('BARBERO_PHONE_NUMBER')
                        if barber_phone:
                            whatsapp_manager.send_approval_request_to_barber(
                                barber_phone=barber_phone,
                                client_name=booking_info['nombre'],
                                service=booking_info['servicio'],
                                date=parsed_date,
                                time=parsed_time,
                                event_id=event_id
                            )
                        
                        # Responder al cliente
                        response_text = (
                            f"¡Perfecto! 🎯 He apartado esa hora para vos.\n\n"
                            f"Para confirmar, debo enviarle una solicitud al barbero. "
                            f"Te avisaré en unos minutos cuando te confirme. 💈\n\n"
                            f"📅 {parsed_date} a las {parsed_time}\n"
                            f"✂️ {booking_info['servicio']}"
                        )
                    else:
                        response_text = "Hubo un error al crear la solicitud. Por favor, intentá de nuevo o escribinos directamente."
                else:
                    # Hora no disponible, ofrecer alternativas
                    if available_hours:
                        hours_str = ", ".join(available_hours[:5])
                        response_text = f"⚠️ Esa hora ya está ocupada. Pero tengo estos horarios disponibles para {parsed_date}: {hours_str}. ¿Cuál preferís?"
                    else:
                        response_text = f"⚠️ No hay turnos disponibles para {parsed_date}. ¿Querés ver otra fecha?"
        
        # Enviar respuesta al cliente
        if whatsapp_manager:
            whatsapp_manager.send_message(phone_number, response_text)
        
        return jsonify({'status': 'success', 'response': response_text})
    
    except Exception as e:
        print(f"❌ Error en webhook: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/webhook/approval', methods=['POST'])
def approval_webhook():
    """
    Webhook para recibir aprobación/rechazo del barbero
    Puede ser llamado desde Evolution API cuando el barbero responde
    """
    try:
        data = request.json
        print(f"📥 Respuesta del barbero: {json.dumps(data, indent=2)}")
        
        # Extraer información
        phone_number = data.get('phone_number', '')
        message_text = data.get('message', '').strip()
        
        # Verificar si es el número del barbero
        barber_phone = os.getenv('BARBERO_PHONE_NUMBER')
        if phone_number != barber_phone:
            return jsonify({'status': 'error', 'message': 'No autorizado'}), 403
        
        # Buscar solicitud pendiente (en producción buscar en base de datos)
        # En este ejemplo simple, esperamos que el barbero incluya el ID del evento
        import re
        event_id_match = re.search(r'(\w+)', message_text)
        
        # Para simplicidad, usamos la última solicitud pendiente
        if not pending_requests:
            return jsonify({'status': 'error', 'message': 'No hay solicitudes pendientes'}), 400
        
        # Obtener la última solicitud
        last_event_id = list(pending_requests.keys())[-1]
        request_data = pending_requests[last_event_id]
        
        if '1' in message_text or 'aprobar' in message_text.lower():
            # APROBAR
            if calendar_manager.confirm_booking(last_event_id):
                # Notificar al cliente
                if whatsapp_manager:
                    whatsapp_manager.send_confirmation_to_client(
                        client_phone=request_data['client_phone'],
                        client_name=request_data['client_name'],
                        service=request_data['service'],
                        date=request_data['date'],
                        time=request_data['time']
                    )
                
                # Eliminar de pendientes
                del pending_requests[last_event_id]
                
                return jsonify({'status': 'success', 'action': 'approved'})
            else:
                return jsonify({'status': 'error', 'message': 'Error confirmando evento'}), 500
        
        elif '2' in message_text or 'rechazar' in message_text.lower():
            # RECHAZAR
            if calendar_manager.cancel_booking(last_event_id):
                # Notificar al cliente
                if whatsapp_manager:
                    whatsapp_manager.send_rejection_to_client(
                        client_phone=request_data['client_phone'],
                        client_name=request_data['client_name'],
                        service=request_data['service'],
                        date=request_data['date'],
                        time=request_data['time']
                    )
                
                # Eliminar de pendientes
                del pending_requests[last_event_id]
                
                return jsonify({'status': 'success', 'action': 'rejected'})
            else:
                return jsonify({'status': 'error', 'message': 'Error cancelando evento'}), 500
        
        return jsonify({'status': 'error', 'message': 'Respuesta no válida. Usá 1 para aprobar o 2 para rechazar'}), 400
    
    except Exception as e:
        print(f"❌ Error en webhook de aprobación: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar estado del servicio"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'calendar': calendar_manager is not None,
            'ai': barber_ai is not None,
            'whatsapp': whatsapp_manager is not None
        }
    })

if __name__ == '__main__':
    print("🚀 Iniciando MaccielBarber Bot...")
    initialize_components()
    
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(host='0.0.0.0', port=port, debug=debug)
