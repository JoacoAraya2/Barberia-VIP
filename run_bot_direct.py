# run_bot_direct.py
# Este script ejecuta el bot en modo consola para pruebas inmediatas sin webhooks complejos
from calendar_manager import CalendarManager
from barber_ai import BarberAI
from whatsapp_manager import WhatsAppManager
import time

def main():
    print("💈 Iniciando MaccielBarber Bot (Versión Gratuita Local)...")
    
    calendar = CalendarManager()
    ai = BarberAI()
    whatsapp = WhatsAppManager()
    
    # Simulación de un cliente escribiendo
    # En un futuro, aquí conectarías una biblioteca que escuche WhatsApp Web en tiempo real
    # Por ahora, probaremos el flujo manual
    
    print("\n--- MODO PRUEBA ---")
    client_phone = input("Ingresa el número del cliente (con código país, ej: 521...): ")
    client_msg = input("Simula el mensaje del cliente: ")
    
    print("\n🤖 IA Pensando...")
    response = ai.generate_response(client_msg)
    print(f"💬 Respuesta de la IA: {response}")
    
    # Verificar si hay acción de reserva
    action = ai.parse_action(response)
    
    if action and action.get('action') == 'create_pending':
        print("📅 Creando cita pendiente en Google Calendar...")
        event_id = calendar.create_pending_booking(
            action.get('name', 'Cliente'),
            action.get('service', 'Corte'),
            action.get('date', '2023-12-01'), # Ajustar lógica de fecha real
            action.get('time', '10')
        )
        if event_id:
            final_msg = f"✅ ¡Solicitud creada! Cita pendiente de aprobación."
        else:
            final_msg = "❌ Error al crear la cita."
    else:
        final_msg = response.split('```')[0].strip()

    confirm = input(f"\n¿Enviar este mensaje a {client_phone}? (s/n): \n{final_msg}\n> ")
    
    if confirm.lower() == 's':
        whatsapp.send_message(client_phone, final_msg)
        print("🚀 Mensaje enviado.")
    else:
        print("❌ Envío cancelado.")

if __name__ == "__main__":
    main()