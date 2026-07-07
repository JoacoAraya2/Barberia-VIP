# MaccielBarber - n8n Workflow Configuration

## Overview
Este documento describe la arquitectura completa para implementar el asistente virtual de MaccielBarber usando n8n, WhatsApp Business API, Google Calendar y un Agente de IA.

---

## 📋 PARTE 1: System Prompt para el Agente de IA

**Ubicación**: Nodo "AI Agent" en n8n (campo "System Message")

```text
Eres el asistente virtual oficial de "MaccielBarber", una barbería de alta calidad. 
Tu tono es profesional, amable, directo y con un toque urbano/moderno propio de una barbería de prestigio.

OBJETIVOS PRINCIPALES:
1. Consultar disponibilidad del barbero en tiempo real.
2. Agendar, reprogramar o cancelar citas.
3. Informar si el barbero está ocupado (cortando) o disponible.
4. NUNCA confirmar una cita sin aprobación previa del barbero.

HERRAMIENTAS DISPONIBLES:
- check_availability(date): Consulta huecos libres en Google Calendar.
- get_current_status(): Verifica si el barbero está ocupado o libre AHORA.
- create_pending_booking(details): Crea evento "PENDIENTE_DE_APROBACION".
- send_approval_request(booking_id): Envía solicitud de aprobación al barbero.

REGLAS DE CONVERSACIÓN:

1. SALUDO INICIAL:
   "¡Hola! 👋 Soy el asistente de MaccielBarber 💈. ¿En qué puedo ayudarte hoy? (Agendar cita, ver horarios, consultar estado)"

2. RECOLECCIÓN DE DATOS (para agendar):
   Debes obtener: Nombre del cliente, Servicio (Corte/Barba/Combo), Fecha deseada, Hora preferida.

3. VERIFICACIÓN DE DISPONIBILIDAD:
   - ANTES de ofrecer cualquier hora, usa `check_availability`.
   - Si la hora pedida está ocupada, sugiere las 3 horas libres más cercanas.
   - No inventes horarios. Confía ciegamente en la herramienta.

4. FLUJO DE CONFIRMACIÓN (CRÍTICO):
   a) Cuando el cliente elija una hora disponible:
      - Ejecuta `create_pending_booking` con título: "🔴 PENDIENTE: [Nombre] - [Servicio]"
   b) Inmediatamente ejecuta `send_approval_request`.
   c) Responde al cliente EXACTAMENTE así:
      "¡Perfecto! He apartado esa hora ⏳. Para confirmar, debo enviarle una solicitud al barbero. Te avisaré en unos minutos."
   d) ESPERA la respuesta del barbero (esto lo maneja el Flujo 2).
   e) Si el barbero APRUEBA: Actualiza calendario a "✅ CONFIRMADO" y avisa al cliente.
   f) Si el barbero RECHAZA: Borra/bloquea el evento y avisa al cliente ofreciendo otras opciones.

5. ESTADO EN TIEMPO REAL:
   Si el cliente pregunta "¿Está cortando ahora?" o similar:
   - Usa `get_current_status`.
   - Si está ocupado: "El barbero está en medio de un corte ahora mismo 💈. Te dejo agendado para [hora] o puedes esperar, ¿qué prefieres?"
   - Si está libre: "¡El barbero está disponible ahora! ¿Quieres pasar ya o agendar para después? ✂️"

6. FORMATO DE MENSAJES:
   - Cortos, claros, aptos para WhatsApp.
   - Emojis moderados: 💈 ✂️ 📅 ✅ ❌ ⏳ 👋
   - No uses párrafos largos.

RESTRICCIONES ABSOLUTAS:
- ❌ NO confirmes citas directamente.
- ❌ NO inventes horarios disponibles.
- ❌ NO saltes el paso de aprobación del barbero.
- ✅ SIEMPRE verifica con `check_availability` antes de ofrecer.
- ✅ SIEMPRE crea evento "PENDIENTE" primero.
```

---

## 🔧 PARTE 2: Configuración de Herramientas (Tools) en n8n

### Tool 1: `check_availability`
**Tipo**: HTTP Request / Google Calendar Node  
**Propósito**: Consultar eventos existentes en una fecha específica.

**Configuración**:
- **Resource**: Event
- **Operation**: Get Many
- **Calendar ID**: Primary (o ID específico de la barbería)
- **Time Min**: `{date}T00:00:00`
- **Time Max**: `{date}T23:59:59`
- **Single Events**: true
- **Order By**: startTime

**Output Processing** (Code Node):
```javascript
// Extrae horas ocupadas y calcula huecos libres
const events = $input.all();
const occupiedSlots = events.map(e => ({
  start: new Date(e.json.start.dateTime || e.json.start.date),
  end: new Date(e.json.end.dateTime || e.json.end.date),
  summary: e.json.summary
}));

// Genera slots de 1 hora desde 09:00 hasta 20:00
const availableSlots = [];
const workStart = 9; // 9 AM
const workEnd = 20;  // 8 PM

for (let hour = workStart; hour < workEnd; hour++) {
  const slotStart = new Date($json.date);
  slotStart.setHours(hour, 0, 0, 0);
  
  const isOccupied = occupiedSlots.some(slot => 
    (slotStart >= slot.start && slotStart < slot.end) ||
    (slotStart <= slot.start && new Date(slotStart.getTime() + 60*60*1000) > slot.start)
  );
  
  if (!isOccupied && !slotStart.toISOString().startsWith($json.date)) {
    // Verificar que no sea día pasado
    const today = new Date().toISOString().split('T')[0];
    if (slotStart.toISOString().split('T')[0] >= today) {
      availableSlots.push(slotStart.toTimeString().substring(0,5));
    }
  }
}

return { json: { available: availableSlots.slice(0, 10), occupied: occupiedSlots } };
```

---

### Tool 2: `get_current_status`
**Tipo**: Google Calendar Node + Code Node  
**Propósito**: Verificar si hay un evento activo EN ESTE MOMENTO.

**Configuración**:
- **Resource**: Event
- **Operation**: Get Many
- **Time Min**: `{now}` (ISO string actual)
- **Time Max**: `{now + 1 hour}`
- **Max Results**: 1

**Logic**:
```javascript
const events = $input.all();
const now = new Date();

if (events.length > 0) {
  const currentEvent = events[0].json;
  const eventStart = new Date(currentEvent.start.dateTime);
  const eventEnd = new Date(currentEvent.end.dateTime);
  
  if (now >= eventStart && now <= eventEnd) {
    return { json: { status: 'busy', event: currentEvent.summary } };
  }
}

return { json: { status: 'free' } };
```

---

### Tool 3: `create_pending_booking`
**Tipo**: Google Calendar Node  
**Propósito**: Crear evento con estado pendiente.

**Configuración**:
- **Resource**: Event
- **Operation**: Create
- **Calendar ID**: Primary
- **Summary**: `🔴 PENDIENTE: {{ $json.client_name }} - {{ $json.service }}`
- **Start Time**: `{{ $json.date }}T{{ $json.time }}:00`
- **End Time**: Calcular según servicio:
  - Corte: +45 min
  - Barba: +30 min
  - Combo: +75 min
- **Description**:
```json
{
  "client_name": "{{ $json.client_name }}",
  "client_phone": "{{ $json.phone }}",
  "service": "{{ $json.service }}",
  "status": "PENDING_APPROVAL",
  "booking_id": "{{ $generateId() }}",
  "created_at": "{{ $now }}"
}
```

---

### Tool 4: `send_approval_request`
**Tipo**: Webhook / HTTP Request  
**Propósito**: Disparar el Flujo 2 de aprobación.

**Configuración**:
- **Method**: POST
- **URL**: `https://tu-n8n-instance.com/webhook/barber-approval`
- **Body** (JSON):
```json
{
  "booking_id": "{{ $json.booking_id }}",
  "client_name": "{{ $json.client_name }}",
  "client_phone": "{{ $json.phone }}",
  "service": "{{ $json.service }}",
  "date": "{{ $json.date }}",
  "time": "{{ $json.time }}",
  "event_id": "{{ $json.event_id }}"
}
```

---

## 🔄 PARTE 3: Flujo 2 - Aprobación del Barbero

### Trigger: Webhook
- **HTTP Method**: POST
- **Path**: `/webhook/barber-approval`
- **Response Mode**: Last Node

### Paso 1: Enviar mensaje al barbero (WhatsApp)
**Nodo**: HTTP Request (WhatsApp Business API)  
**Endpoint**: `https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages`

**Body**:
```json
{
  "messaging_product": "whatsapp",
  "to": "{BARBER_PHONE_NUMBER}",
  "type": "text",
  "text": {
    "body": "💈 *Nueva solicitud en MaccielBarber*\n\n👤 Cliente: {{ $json.client_name }}\n✂️ Servicio: {{ $json.service }}\n📅 Fecha: {{ $json.date }}\n⏰ Hora: {{ $json.time }}\n\n*Responde:* \n1️⃣ para APROBAR\n2️⃣ para RECHAZAR"
  }
}
```

### Paso 2: Esperar respuesta del barbero
**Opción A**: Usar otro Webhook Trigger (si WhatsApp envía webhook al recibir respuesta)  
**Opción B**: Usar nodo "Wait" + Polling (menos recomendado)

**Recomendado**: Configurar WhatsApp Business API para enviar webhooks a n8n cuando el barbero responde.

**Webhook de Respuesta**:
- **Path**: `/webhook/barber-reply`
- **Extract**: Número del barbero + texto del mensaje

### Paso 3: Procesar respuesta (Switch Node)
**Condition**:
- **Route 1 (Aprobar)**: `{{ $json.message == "1" || $json.message.toLowerCase().includes("aprobar") }}`
- **Route 2 (Rechazar)**: `{{ $json.message == "2" || $json.message.toLowerCase().includes("rechazar") }}`

---

#### Route 1: Aprobar ✅

**Paso 1.1**: Actualizar evento en Google Calendar
- **Resource**: Event
- **Operation**: Update
- **Event ID**: `{{ $json.event_id }}`
- **New Summary**: `✅ CONFIRMADO: {{ $json.client_name }} - {{ $json.service }}`
- **Update Description**: Add `"status": "CONFIRMED"`

**Paso 1.2**: Notificar al cliente
```json
{
  "messaging_product": "whatsapp",
  "to": "{{ $json.client_phone }}",
  "type": "text",
  "text": {
    "body": "✅ ¡Tu cita ha sido *CONFIRMADA* por el barbero!\n\n📅 Fecha: {{ $json.date }}\n⏰ Hora: {{ $json.time }}\n💈 Lugar: MaccielBarber\n\n¡Te esperamos! ✂️"
  }
}
```

---

#### Route 2: Rechazar ❌

**Paso 2.1**: Eliminar/Bloquear evento en Google Calendar
- **Opción A**: Delete Event
- **Opción B**: Update Summary a `❌ RECHAZADO: ...`

**Paso 2.2**: Notificar al cliente
```json
{
  "messaging_product": "whatsapp",
  "to": "{{ $json.client_phone }}",
  "type": "text",
  "text": {
    "body": "❌ Lo sentimos, el barbero no puede atenderte a esa hora por un imprevisto.\n\n¿Te gustaría ver otros horarios disponibles? 📅\n\nResponde 'SI' para buscar otra hora."
  }
}
```

**Paso 2.3** (Opcional): Re-iniciar conversación con Agente IA
- Enviar webhook al Flujo 1 para notificar que debe ofrecer nuevas horas.

---

## ⚙️ PARTE 4: Configuración Técnica Adicional

### 1. Zona Horaria
- **n8n Settings**: `TIMEZONE=America/Montevideo` (o la local de tu barbería)
- **Google Calendar**: Verificar configuración de zona horaria en settings del calendario.
- **AI Agent**: Especificar zona horaria en el system prompt.

### 2. Memoria del Agente (Window Buffer Memory)
- **Key**: `session_{{ $json.from }}` (número de WhatsApp del cliente)
- **Max Messages**: 10
- **Purpose**: Recordar nombre, servicio elegido, y estado de la reserva dentro de la misma conversación.

### 3. Manejo de IDs Únicos
Usar generación de UUID para cada booking:
```javascript
// En nodo Code antes de crear evento
const bookingId = crypto.randomUUID();
return { json: { ...$json, booking_id: bookingId } };
```

### 4. Duración de Servicios
Definir en el AI Agent o en un nodo Code:
```javascript
const serviceDuration = {
  'Corte': 45,
  'Barba': 30,
  'Combo': 75
};
const duration = serviceDuration[$json.service] || 45;
```

### 5. Rate Limiting y Delays
- Agregar nodo "Wait" de 2 segundos entre creación de evento y envío de notificación.
- Evitar race conditions cuando el barbero responde rápidamente.

---

## 🧪 PARTE 5: Testing y Debugging

### Casos de Prueba

1. **Agendamiento Exitoso**:
   - Cliente pide hora disponible → Crea pendiente → Barbero aprueba → Cliente recibe confirmación.

2. **Hora Ocupada**:
   - Cliente pide hora ocupada → IA sugiere 3 alternativas → Cliente elige otra → Sigue flujo normal.

3. **Rechazo del Barbero**:
   - Cliente elige hora → Barbero rechaza → Cliente recibe notificación de rechazo → IA ofrece nuevas horas.

4. **Consulta de Estado**:
   - Cliente pregunta "¿Está cortando ahora?" → IA verifica calendario → Responde según estado real.

5. **Doble Reserva**:
   - Dos clientes piden la misma hora simultáneamente → Segundo cliente recibe mensaje de "hora ocupada".

### Logs Recomendados
- Habilitar logs en n8n para todos los nodos de Google Calendar.
- Guardar historial de aprobaciones/rechazos en una hoja de Google Sheets o base de datos.

---

## 📞 Integración con WhatsApp

### Opción A: WhatsApp Business Cloud API (Meta)
- **Ventajas**: Oficial, estable, sin costos de terceros (solo costo por conversación).
- **Requisitos**: 
  - Meta Business Account verificado.
  - Número de teléfono dedicado.
  - Plantillas aprobadas para mensajes proactivos (si el barbero inicia la conversación).
- **Nota**: Si el cliente escribe primero, puedes responder con texto libre sin plantillas.

### Opción B: Twilio WhatsApp API
- **Ventajas**: Más fácil de configurar, sandbox para testing.
- **Desventajas**: Costo adicional por mensaje.

### Opción C: Evolution API / Baileys (Self-hosted)
- **Ventajas**: Gratis, control total.
- **Desventajas**: Requiere mantener sesión activa, riesgo de bloqueo por WhatsApp.

---

## 🛡️ Seguridad y Buenas Prácticas

1. **Validación de Entradas**: Sanitizar nombres y teléfonos antes de guardar en calendario.
2. **Rate Limiting**: Limitar solicitudes de agendamiento por número de teléfono (ej. máx 3 citas pendientes por cliente).
3. **Backup**: Exportar eventos de Google Calendar diariamente a una hoja de cálculo.
4. **Timeout**: Si el barbero no responde en 10 minutos, enviar recordatorio automático.
5. **Cancelaciones**: Permitir que el cliente cancele vía WhatsApp (IA borra evento si está pendiente o confirmado).

---

## 📄 Ejemplo de Estructura de Eventos en Google Calendar

| Título | Descripción | Estado | Color |
|--------|-------------|--------|-------|
| 🔴 PENDIENTE: Juan - Corte | `{"client": "Juan", "phone": "...", "status": "PENDING"}` | Pendiente | Rojo |
| ✅ CONFIRMADO: Juan - Corte | `{"client": "Juan", "phone": "...", "status": "CONFIRMED"}` | Confirmado | Verde |
| ❌ RECHAZADO: Juan - Corte | `{"client": "Juan", "phone": "...", "status": "REJECTED"}` | Rechazado | Gris |
| 💈 CORTE: María - Confirmado | `{"client": "María", "status": "CONFIRMED"}` | Confirmado | Azul |

---

## 🚀 Pasos de Implementación

1. **Configurar Google Calendar API** en Google Cloud Console.
2. **Crear credenciales OAuth2** para n8n acceder a Calendar.
3. **Configurar WhatsApp Business API** (Meta o Twilio).
4. **Importar flujos en n8n** (Flujo 1: IA + Calendar, Flujo 2: Aprobación).
5. **Probar en sandbox** con números de prueba.
6. **Lanzar a producción** con números reales.
7. **Monitorear** las primeras 50 interacciones para ajustar respuestas de la IA.

---

*Documento creado para MaccielBarber - Sistema de Agendamiento Inteligente con n8n*
*Versión: 1.0 | Fecha: 2025*
