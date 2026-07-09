#!/usr/bin/env python3
"""
Script para probar la API de WhatsApp Business (Meta oficial)
Paso 1: Modo de prueba

Instrucciones:
1. Genera tu Access Token temporal en el panel de Meta Developers
2. Agrega tu número personal como "Número de prueba" en el panel
3. Ejecuta este script para enviar un mensaje de prueba
"""

import os
import requests
from dotenv import load_dotenv

# Cargar configuración de test
load_dotenv('config/.env.test')

def send_test_message():
    """Envía un mensaje de prueba usando la API oficial de WhatsApp Business"""

    # Obtener configuración
    api_url = os.getenv('WHATSAPP_API_URL', 'https://graph.facebook.com/v21.0')
    phone_number_id = os.getenv('PHONE_NUMBER_ID')
    access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    to_number = os.getenv('TEST_TO_NUMBER')

    if not access_token or access_token == 'TU_ACCESS_TOKEN_AQUI':
        print("❌ Error: Debes configurar el WHATSAPP_ACCESS_TOKEN en config/.env.test")
        print("\n📋 Pasos:")
        print("1. Ve al panel de Meta Developers")
        print("2. En 'Paso 1. Probar', haz clic en 'Generar identificador de acceso'")
        print("3. Copia el token y pégalo en config/.env.test")
        return False

    if not phone_number_id:
        print("❌ Error: PHONE_NUMBER_ID no configurado")
        return False

    if not to_number:
        print("❌ Error: TEST_TO_NUMBER no configurado")
        return False

    # Endpoint para enviar mensajes
    endpoint = f"{api_url}/{phone_number_id}/messages"

    # Headers
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # Payload del mensaje
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": "👋 ¡Hola! Este es un mensaje de prueba desde MaccielBarber Bot.\n\nSi recibiste este mensaje, la API de WhatsApp está funcionando correctamente. ✅\n\n💈 MaccielBarber - Tu barbero inteligente"
        }
    }

    print(f"📤 Enviando mensaje de prueba a: {to_number}")
    print(f"🔗 Endpoint: {endpoint}")
    print(f"📱 Phone Number ID: {phone_number_id}")

    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=10)

        print(f"\n📊 Respuesta HTTP: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ ¡Mensaje enviado con éxito!")
            print(f"📬 Message ID: {result.get('messages', [{}])[0].get('id', 'N/A')}")
            return True
        else:
            print(f"❌ Error al enviar mensaje:")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")

            # Ayuda para errores comunes
            if response.status_code == 401:
                print("\n⚠️ Error 401: Token inválido o expirado")
                print("   → Genera un nuevo token en el panel de Meta")
            elif response.status_code == 403:
                print("\n⚠️ Error 403: Permiso denegado")
                print("   → Verifica que el número de destino esté agregado como 'Número de prueba'")
            elif response.status_code == 404:
                print("\n⚠️ Error 404: Phone Number ID incorrecto")
                print("   → Verifica el PHONE_NUMBER_ID en config/.env.test")

            return False

    except requests.exceptions.Timeout:
        print("❌ Timeout: La solicitud tardó demasiado")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False


def check_phone_number_status():
    """Verifica el estado del número de teléfono"""

    api_url = os.getenv('WHATSAPP_API_URL', 'https://graph.facebook.com/v21.0')
    phone_number_id = os.getenv('PHONE_NUMBER_ID')
    access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')

    if not access_token or access_token == 'TU_ACCESS_TOKEN_AQUI':
        print("⚠️ No se puede verificar sin un access token válido")
        return None

    endpoint = f"{api_url}/{phone_number_id}"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    params = {
        'fields': 'display_phone_number,quality_rating,verified_name,status'
    }

    try:
        response = requests.get(endpoint, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            print("\n📱 Estado del número:")
            print(f"   Número: {data.get('display_phone_number', 'N/A')}")
            print(f"   Estado: {data.get('status', 'N/A')}")
            print(f"   Calidad: {data.get('quality_rating', 'N/A')}")
            print(f"   Nombre verificado: {data.get('verified_name', 'N/A')}")
            return data
        else:
            print(f"Error verificando estado: {response.status_code}")
            return None

    except Exception as e:
        print(f"Error verificando estado: {e}")
        return None


if __name__ == '__main__':
    print("=" * 60)
    print("💈 MaccielBarber - Prueba de API de WhatsApp")
    print("Paso 1: Modo Test")
    print("=" * 60)
    print()

    # Verificar estado del número
    print("🔍 Verificando estado del número...")
    check_phone_number_status()

    print("\n" + "=" * 60)

    # Enviar mensaje de prueba
    print("\n📤 Enviando mensaje de prueba...\n")
    success = send_test_message()

    print("\n" + "=" * 60)
    if success:
        print("✅ ¡Prueba completada exitosamente!")
        print("\n📝 Próximos pasos:")
        print("   1. Verifica que llegué el mensaje al número de prueba")
        print("   2. Continúa con el Paso 2: Configuración de producción")
    else:
        print("❌ La prueba falló. Revisa los errores arriba.")
        print("\n📋 Checklist:")
        print("   □ ¿Generaste el Access Token en el panel de Meta?")
        print("   □ ¿Agregaste tu número como 'Número de prueba'?")
        print("   □ ¿Configuraste el token en config/.env.test?")
    print("=" * 60)