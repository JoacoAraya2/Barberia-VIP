from flask import Flask, request, jsonify
from calendar_manager import CalendarManager
from barber_ai import BarberAI
from whatsapp_manager import WhatsAppManager
import os

app = Flask(__name__)

# ✅ DEFINICIÓN GLOBAL EXPLÍCITA
user_contexts = {} 

# Inicializar componentes
try:
    calendar = CalendarManager()
    ai = BarberAI()
    whatsapp = WhatsAppManager()
    print("✅ Componentes inicializados correctamente")
except Exception as e:
    print(f"⚠️ Error al inicializar componentes: {e}")
    calendar = None
    ai = None
    whatsapp = None

# 🔑 TOKEN DE VERIFICACIÓN
VERIFY_TOKEN = "macciell2024"

@app.route('/webhook/whatsapp', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print("✅ [WEBHOOK] Verificación exitosa por Meta!")
        return challenge, 200
    else:
        print(f"❌ [WEBHOOK] Fallo en verificación. Mode: {mode}, Token recibido: {token}")
        return "Forbidden: Verify token mismatch", 403

@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    data = request.json
    
    # LOGS PARA DEPURACIÓN
    print("\n--- 🔥 DATO BRUTO RECIBIDO ---")
    print(data) 
    print("--------------------------")

    try:
        entry = data.get('entry', [])
        if not entry:
            return jsonify({"status": "no entry"}), 200
            
        changes = entry[0].get('changes', [])
        if not changes:
            return jsonify({"status": "no changes"}), 200
            
        value = changes[0].get('value', {})
        messages = value.get('messages', [])
        
        if not messages:
            statuses = value.get('statuses', [])
            if statuses:
                print(f"📩 Actualización de estado: {statuses[0].get('status')}")
            return jsonify({"status": "no new messages"}), 200

        msg_obj = messages[0]
        sender = msg_obj.get('from', '')
        msg_type = msg_obj.get('type', '')
        
        text = ""
        if msg_type == 'text':
            text = msg_obj.get('text', {}).get('body', '')
        elif msg_type == 'button':
            text = msg_obj.get('button', {}).get('text', '')
        elif msg_type == 'interactive':
            interaction = msg_obj.get('interactive', {})
            if interaction.get('type') == 'button_reply':
                text = interaction.get('button_reply', {}).get('title', '')
            elif interaction.get('type') == 'list_reply':
                text = interaction.get('list_reply', {}).get('title', '')

        if not text or not sender:
            print(f"⚠️ Mensaje ignorado: Sin texto útil. Sender: {sender}")
            return jsonify({"status": "ignored"}), 200

        print(f"✅ MENSAJE RECIBIDO de {sender}: {text}")

        # --- LÓGICA DEL BOT CON PROTECCIÓN DE ERRORES ---
        if ai is None:
            print("❌ Error: AI no está inicializada.")
            return jsonify({"status": "ai_not_loaded"}), 500

        try:
            # 1. Obtener respuesta de IA
            # Aseguramos que user_contexts exista para este sender
            if sender not in user_contexts:
                user_contexts[sender] = []
            
            context = user_contexts[sender]
            
            # Llamar a la IA
            ai_response_text = ai.generate_response(text, context)
            
            # Actualizar contexto
            context.append({"role": "user", "content": text})
            context.append({"role": "assistant", "content": ai_response_text})
            user_contexts[sender] = context[-10:] 

            # 2. Verificar acción
            action = ai.parse_action(ai_response_text)
            
            final_reply = ai_response_text.split('```')[0].strip()

            if action:
                act_type = action.get('action')
                if act_type == 'check_availability':
                    final_reply += "\n\n💈 He consultado la agenda. Parece que hay espacio. ¿Procedo a reservar como PENDIENTE?"
                
                elif act_type == 'create_pending':
                    if calendar:
                        try:
                            eid = calendar.create_pending_booking(
                                action.get('name'), 
                                action.get('service'), 
                                action.get('date'), 
                                action.get('time')
                            )
                            if eid:
                                final_reply = f"✅ ¡Solicitud creada! Estado PENDIENTE."
                        except Exception as e_cal:
                            print(f"Error calendario: {e_cal}")
                            final_reply += "\n⚠️ Error al reservar."
                    else:
                        final_reply += "\n⚠️ Calendario no disponible."

            # 3. Enviar respuesta
            if whatsapp:
                print(f"📤 Enviando respuesta: {final_reply}")
                whatsapp.send_message(sender, final_reply)
            else:
                print("⚠️ WhatsApp Manager no disponible.")

            return jsonify({"status": "processed"}), 200

        except AttributeError as e_attr:
            print(f"❌ ERROR DE MÉTODO EN IA: {e_attr}")
            print("⚠️ Probablemente falta 'generate_response' o 'parse_action' en barber_ai.py")
            # Enviamos un mensaje de error al usuario para avisar
            if whatsapp:
                whatsapp.send_message(sender, "⚠️ Error interno del bot: La IA no está configurada correctamente.")
            return jsonify({"status": "ai_error"}), 500
            
        except Exception as e_inner:
            print(f"❌ ERROR INTERNO EN LÓGICA: {e_inner}")
            return jsonify({"status": "error"}), 500

    except Exception as e:
        print(f"❌ ERROR CRÍTICO WEBHOOK: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Iniciando MaccielBarber Bot...")
    print(f"🔑 Token: {VERIFY_TOKEN}")
    app.run(host='0.0.0.0', port=5000, debug=True)