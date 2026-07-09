# MaccielBarber Bot - Chatbot Gratuito para Barbería

Chatbot inteligente para gestión de turnos en barberías, desarrollado con tecnologías 100% gratuitas.

## 🚀 Características

- **Atención automática 24/7** vía WhatsApp
- **Gestión de turnos** con Google Calendar
- **Aprobación manual** del barbero antes de confirmar
- **IA integrada** (Ollama local o Google Gemini gratuito)
- **Detección de disponibilidad** en tiempo real
- **Flujo completo**: agendar → pendiente → aprobar/rechazar → notificar

## 📁 Estructura del Proyecto

```
maccielbarber-bot/
├── src/
│   ├── app.py                 # Aplicación Flask principal
│   ├── calendar_manager.py    # Gestión de Google Calendar
│   ├── barber_ai.py           # Sistema de IA para respuestas
│   └── whatsapp_manager.py    # Integración con Evolution API
├── config/
│   ├── .env.example           # Plantilla de variables de entorno
│   └── credentials.json       # Credenciales de Google (no incluir en git)
├── data/                      # Datos persistentes (opcional)
├── logs/                      # Logs del sistema
├── requirements.txt           # Dependencias de Python
└── README.md                  # Este archivo
```

## 🛠️ Instalación

### 1. Prerrequisitos

- Python 3.8+
- Docker (para Evolution API)
- Cuenta de Google
- Ngrok (para exponer localmente)

### 2. Instalar dependencias

```bash
cd maccielbarber-bot
pip install -r requirements.txt
```

### 3. Configurar Google Calendar API

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto
3. Habilita la API de Google Calendar
4. Crea una cuenta de servicio (Service Account)
5. Descarga el JSON de credenciales como `config/credentials.json`
6. Comparte tu calendario de Google con el email de la cuenta de servicio

### 4. Configurar Evolution API (WhatsApp)

```bash
# Clonar Evolution API
git clone https://github.com/EvolutionAPI/evolution-api.git
cd evolution-api

# Configurar con Docker
docker-compose up -d

# Escanea el QR desde la interfaz web (puerto 8080)
```

### 5. Configurar variables de entorno

```bash
cp config/.env.example config/.env
```

Edita `config/.env` con tus datos:

```env
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_INSTANCE_NAME=maccielbarber
EVOLUTION_API_KEY=tu_api_key_generada

GOOGLE_CALENDAR_ID=tu_calendar_id@group.calendar.google.com
GOOGLE_SERVICE_ACCOUNT_FILE=config/credentials.json

BARBERO_PHONE_NUMBER=5491112345678
TIMEZONE=America/Argentina/Buenos_Aires
FLASK_PORT=5000
```

### 6. Exponer con Ngrok (gratis)

```bash
# Instalar ngrok si no lo tenés
# Descargar desde https://ngrok.com/

# Ejecutar ngrok
ngrok http 5000
```

Guarda la URL pública que te da ngrok (ej: `https://abc123.ngrok.io`)

## 🚀 Ejecución

### Opción A: Con IA local (Ollama)

```bash
# Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Descargar modelo
ollama pull llama2

# Ejecutar bot
python src/app.py
```

### Opción B: Con Google Gemini (gratis)

Obtén tu API Key en [Google AI Studio](https://makersuite.google.com/) y agrega a `.env`:

```env
AI_MODEL=gemini
GEMINI_API_KEY=tu_api_key_de_gemini
```

### Opción C: Modo básico (sin IA externa)

Funciona con reglas predefinidas, ideal para testing:

```bash
python src/app.py
```

## ⚙️ Configurar Webhook en Evolution API

1. Abre la interfaz web de Evolution API (http://localhost:8080)
2. Ve a la sección de webhooks de tu instancia
3. Configura el webhook apuntando a: `https://tu-url-ngrok.ngrok.io/webhook/whatsapp`
4. Guarda los cambios

## 📱 Flujo de Uso

### Para el Cliente:

1. Escribe al WhatsApp de la barbería
2. El bot saluda y ofrece ayuda
3. El cliente pide turno (ej: "Quiero agendar un corte para mañana a las 15hs")
4. El bot verifica disponibilidad
5. Si hay lugar, crea evento "PENDIENTE" y avisa que necesita aprobación
6. El cliente espera confirmación

### Para el Barbero:

1. Recibe WhatsApp con detalles de la solicitud
2. Responde `1` para APROBAR o `2` para RECHAZAR
3. El sistema actualiza el calendario y notifica al cliente automáticamente

## 🔧 Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/webhook/whatsapp` | POST | Recibe mensajes de clientes |
| `/webhook/approval` | POST | Recibe aprobación/rechazo del barbero |
| `/health` | GET | Verifica estado del servicio |

## 🧪 Testing Manual

Probar sin WhatsApp usando curl:

```bash
# Probar salud del servicio
curl http://localhost:5000/health

# Simular mensaje de cliente
curl -X POST http://localhost:5000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "key": {"remoteJid": "5491112345678@s.whatsapp.net"},
    "message": {"conversation": "Hola, quiero agendar un corte para hoy a las 16hs"}
  }'
```

## 🔄 Migración Futura a n8n

Este código está diseñado para ser migrado fácilmente a n8n cuando tengas recursos:

- La lógica de `calendar_manager.py` → Nodos de Google Calendar en n8n
- La lógica de `barber_ai.py` → Nodo de Agente IA en n8n
- La lógica de `whatsapp_manager.py` → Nodo de WhatsApp en n8n
- Los webhooks → Triggers de Webhook en n8n

## ⚠️ Consideraciones

- **Almacenamiento**: Las solicitudes pendientes se guardan en memoria. Para producción, usar base de datos (SQLite, PostgreSQL).
- **Seguridad**: No subir `credentials.json` a GitHub. Está en `.gitignore`.
- **Zona horaria**: Asegurar que Google Calendar, el servidor y `.env` usen la misma zona horaria.
- **Recursos**: Ollama requiere RAM (mínimo 4GB recomendado para modelos pequeños).

## 📞 Soporte

Para problemas o consultas, revisar los logs en la consola o en la carpeta `logs/`.

## 📄 Licencia

Uso libre para fines comerciales y personales.

---

**MaccielBarber** 💈 - Tu barbería, siempre disponible.
