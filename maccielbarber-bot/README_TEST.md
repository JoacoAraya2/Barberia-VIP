# 💈 MaccielBarber Bot - Prueba de API de WhatsApp

## Paso 1: Modo Test

Este script te permite probar la API oficial de WhatsApp Business de Meta usando tu número de prueba.

### 📋 Configuración requerida

#### 1. Datos de tu número de prueba (ya los tenés):
- **Número de test**: `+1 (555) 189-2968`
- **Phone Number ID**: `1128271267045355`
- **WhatsApp Business Account ID**: `906754625047026`

#### 2. Generar Access Token:
1. Ve al [Panel de Meta Developers](https://developers.facebook.com/)
2. Selecciona tu aplicación
3. En **"Paso 1. Probar"**, hacé clic en **"Generar identificador de acceso"**
4. Copiá el token generado

#### 3. Configurar el archivo `.env.test`:

Editá el archivo `config/.env.test` y reemplazá:

```bash
WHATSAPP_ACCESS_TOKEN=TU_ACCESS_TOKEN_AQUI
```

Por el token que generaste:

```bash
WHATSAPP_ACCESS_TOKEN=EAA... (token completo)
```

#### 4. Agregar tu número personal como número de prueba:

1. En el panel de Meta, andá a **"Configuración de la aplicación"** → **"WhatsApp" → "Configuración de la API"**
2. En **"Números de prueba"**, agregá tu número personal con código de país (ej: `5491112345678`)
3. Seguí las instrucciones para verificar el número

### 🚀 Ejecutar la prueba

```bash
cd /workspace/maccielbarber-bot
python test_whatsapp_api.py
```

### ✅ Resultado esperado

Si todo está configurado correctamente:

```
============================================================
💈 MaccielBarber - Prueba de API de WhatsApp
Paso 1: Modo Test
============================================================

🔍 Verificando estado del número...

📱 Estado del número:
   Número: +1 (555) 189-2968
   Estado: CONNECTED
   Calidad: GREEN
   Nombre verificado: MaccielBarber

============================================================

📤 Enviando mensaje de prueba...

📤 Enviando mensaje de prueba a: 5491112345678
🔗 Endpoint: https://graph.facebook.com/v21.0/1128271267045355/messages
📱 Phone Number ID: 1128271267045355

📊 Respuesta HTTP: 200
✅ ¡Mensaje enviado con éxito!
📬 Message ID: wamid.HBgLNTQ5MTExMjM0NTY3OBUCABIYIDNFQjBDMTQyRjdBRDQxNzlGNzRBOTVBAA==

============================================================
✅ ¡Prueba completada exitosamente!

📝 Próximos pasos:
   1. Verifica que llegué el mensaje al número de prueba
   2. Continúa con el Paso 2: Configuración de producción
============================================================
```

### 🔧 Solución de problemas

#### Error 401: Token inválido o expirado
- El token temporal dura 24 horas
- Generá uno nuevo en el panel de Meta

#### Error 403: Permiso denegado
- Verificá que tu número personal esté agregado como "Número de prueba"
- Asegurate de haber verificado tu número siguiendo las instrucciones de Meta

#### Error 404: Phone Number ID incorrecto
- Verificá que el `PHONE_NUMBER_ID` en `config/.env.test` sea correcto
- Debería ser: `1128271267045355`

### 📚 Documentación oficial

- [WhatsApp Business Platform Documentation](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Getting Started with the WhatsApp Business Platform](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)

---

**Una vez completada la prueba exitosamente, podés continuar con el Paso 2: Configuración de producción.**
