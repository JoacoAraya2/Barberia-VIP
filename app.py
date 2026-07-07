from flask import Flask, request, jsonify
from calendar_manager import CalendarManager
from barber_ai import BarberAI
from whatsapp_manager import WhatsAppManager
import os

app = Flask(__name__)

# Inicializar componentes
calendar = CalendarManager()
ai = BarberAI()
whatsapp = WhatsAppManager()

# Almacenamiento temporal de contexto (en memoria para demo)
# En producción usar Redis o DB
user_contexts = {} 

@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    data = request.json
    # Adaptar según estructura exacta de Evolution API
    # Generalmente viene en data.message o similar
    message_obj = data.get('message', {})
    sender = message_obj.get('key', {}).get('remoteJid', '')
    text = message_obj.get('message', {}).get('conversation', '')
    
    if not text or not sender:
        return jsonify({"status": "ignored"}), 200

    # 1. Obtener respuesta de IA
    context = user_contexts.get(sender, [])
    ai_response_text = ai.generate_response(text, context)
    
    # Actualizar contexto
    context.append({"role": "user", "content": text})
    context.append({"role": "assistant", "content": ai_response_text})
    user_contexts[sender] = context[-10:] # Guardar últimos 10 mensajes

    # 2. Verificar si la IA quiere ejecutar una acción
    action = ai.parse_action(ai_response_text)
    
    final_reply = ai_response_text.split('```')[0].strip() # Limpiar JSON de la respuesta visible

    if action:
        if action.get('action') == 'check_availability':
            # Simular verificación (aquí llamarías a calendar.check_availability)
            final_reply += "\n\n💈 He consultado la agenda. Parece que hay espacio. ¿Procedo a reservar como PENDIENTE?"
            # Aquí podrías guardar el intento en sesión para el siguiente paso
        
        elif action.get('action') == 'create_pending':
            eid = calendar.create_pending_booking(
                action['name'], action['service'], action['date'], action['time']
            )
            if eid:
                final_reply = f"✅ ¡Solicitud creada! He apartado la hora pero está en estado PENDIENTE. El barbero recibirá una alerta. Te avisaré en cuanto confirme."
                # Aquí dispararías notificación al barbero (email o otro webhook)

    # 3. Enviar respuesta
    whatsapp.send_message(sender, final_reply)
    return jsonify({"status": "processed"}), 200

@app.route('/webhook/approval', methods=['POST'])
def approval_webhook():
    """Recibe la aprobación del barbero (simulado)"""
    data = request.json
    event_id = data.get('event_id')
    approved = data.get('approved') # True/False
    
    if approved:
        calendar.confirm_booking(event_id)
        # Enviar mensaje al cliente confirmando
        msg = "✅ ¡Tu cita ha sido CONFIRMADA por el barbero! Nos vemos pronto."
        # Necesitarías guardar el número del cliente asociado al event_id
    else:
        msg = "❌ El barbero no pudo aprobar la cita. Por favor elige otra hora."
        
    return jsonify({"status": "updated"}), 200

if __name__ == '__main__':
    print("🚀 Iniciando MaccielBarber Bot...")
    app.run(host='0.0.0.0', port=5000, debug=True)