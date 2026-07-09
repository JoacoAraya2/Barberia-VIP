"""
Sistema de IA para MaccielBarber
Usa Ollama (modelo local gratuito) o Google Gemini (capa gratuita) para procesar mensajes
"""

import json
import os
from datetime import datetime
import re

class BarberAI:
    def __init__(self, model='ollama', model_name='llama2'):
        """
        Inicializa el sistema de IA
        
        Args:
            model: 'ollama' para local, 'gemini' para Google Gemini
            model_name: Nombre del modelo a usar
        """
        self.model = model
        self.model_name = model_name
        self.system_prompt = self._get_system_prompt()
        self.conversation_history = {}
    
    def _get_system_prompt(self):
        """Retorna el prompt del sistema con la personalidad de MaccielBarber"""
        return """Eres el asistente virtual oficial de "MaccielBarber", una barbería de alta calidad. 
Tu tono es profesional, amable, directo y con un toque urbano/moderno propio de una barbería de prestigio.

OBJETIVOS:
1. Consultar disponibilidad del barbero
2. Agendar, reprogramar o cancelar citas
3. Informar si el barbero está ocupado o disponible
4. NUNCA confirmar una cita sin aprobación previa del barbero

SERVICIOS DISPONIBLES:
- Corte de cabello (30 min) - $5000
- Barba (20 min) - $3000
- Combo Corte + Barba (45 min) - $7000

FLUJO DE ATENCIÓN:
1. Saluda brevemente mencionando MaccielBarber 💈
2. Para agendar necesitas: Nombre, Servicio, Fecha y Hora
3. Verifica disponibilidad antes de reservar
4. Crea evento como "PENDIENTE" y avisa que necesita aprobación del barbero
5. El barbero aprobará manualmente y el cliente será notificado

REGLAS IMPORTANTES:
- No inventes horarios, usa solo los proporcionados por el sistema
- Nunca confirmes directamente, siempre pasa por aprobación
- Mantén mensajes cortos, claros y con emojis moderados (💈, ✂️, 📅)
- Si el barbero está ocupado, ofrece esperar o agendar para después

FORMATO DE RESPUESTA:
Responde de manera natural como en WhatsApp, sin formato JSON."""

    def get_available_hours_format(self, available_hours):
        """Formatea las horas disponibles para mostrar al cliente"""
        if not available_hours:
            return "No hay turnos disponibles para esa fecha."
        
        # Mostrar máximo 5 opciones
        hours_to_show = available_hours[:5]
        return ", ".join(hours_to_show)
    
    def extract_booking_info(self, message):
        """
        Extrae información de reserva del mensaje del cliente
        
        Returns:
            Dict con nombre, servicio, fecha, hora o None si no hay info completa
        """
        info = {
            'nombre': None,
            'servicio': None,
            'fecha': None,
            'hora': None
        }
        
        # Patrones para extraer información
        # Nombre (después de "me llamo", "soy", etc.)
        nombre_patterns = [
            r'(?:me llamo|mi nombre es|soy|yo soy)\s+([A-Za-zÁÉÍÓÚáéíóúñ]+(?:\s+[A-Za-zÁÉÍÓÚáéíóúñ]+)?)',
            r'^([A-Za-zÁÉÍÓÚáéíóúñ]+(?:\s+[A-Za-zÁÉÍÓÚáéíóúñ]+)?)\s+(?:quiero|necesito|vengo)'
        ]
        
        for pattern in nombre_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                info['nombre'] = match.group(1).strip()
                break
        
        # Servicio
        service_patterns = [
            r'(corte|barba|combo|corte\s+y\s+barba)',
            r'(quiero|necesito)\s+un?\s+(corte|barba|combo)'
        ]
        
        for pattern in service_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                service_raw = match.group(1).lower()
                if 'combo' in service_raw or ('corte' in service_raw and 'barba' in service_raw):
                    info['servicio'] = 'Combo'
                elif 'corte' in service_raw:
                    info['servicio'] = 'Corte'
                elif 'barba' in service_raw:
                    info['servicio'] = 'Barba'
                break
        
        # Fecha (formatos comunes)
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})/(\d{2,4})',  # DD/MM/AAAA o DD/MM/AA
            r'(\d{1,2})-(\d{1,2})-(\d{2,4})',  # DD-MM-AAAA
            r'(hoy|mañana|pasado mañana)',
            r'(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                info['fecha'] = match.group(0)
                break
        
        # Hora
        time_patterns = [
            r'(\d{1,2}):?(\d{2})?\s*(?:am|pm|hs|h|a\.m\.|p\.m\.)?',
            r'a\s+las?\s+(\d{1,2})(?:\s+y\s+(\d{2}))?',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                info['hora'] = match.group(0)
                break
        
        # Verificar si tenemos información completa
        has_complete_info = all([
            info['nombre'],
            info['servicio'],
            info['fecha'],
            info['hora']
        ])
        
        return info if has_complete_info else None
    
    def process_message(self, message, client_id, context=None):
        """
        Procesa un mensaje del cliente y genera respuesta
        
        Args:
            message: Mensaje del cliente
            client_id: Identificador único del cliente (número de teléfono)
            context: Contexto adicional (disponibilidad, estado actual, etc.)
            
        Returns:
            Respuesta generada por la IA
        """
        # Inicializar historial si no existe
        if client_id not in self.conversation_history:
            self.conversation_history[client_id] = []
        
        # Agregar mensaje al historial
        self.conversation_history[client_id].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Mantener solo últimos 10 mensajes para no saturar
        if len(self.conversation_history[client_id]) > 10:
            self.conversation_history[client_id] = self.conversation_history[client_id][-10:]
        
        # Construir prompt con contexto
        context_str = ""
        if context:
            if context.get('available_hours'):
                context_str += f"\n\nHORAS DISPONIBLES: {self.get_available_hours_format(context['available_hours'])}"
            if context.get('current_status'):
                status = context['current_status']
                if status.get('busy'):
                    context_str += f"\n\nESTADO ACTUAL: El barbero está OCUPADO ahora (hasta las {status['current_event']['end']})"
                else:
                    context_str += "\n\nESTADO ACTUAL: El barbero está DISPONIBLE ahora"
        
        full_prompt = f"{self.system_prompt}{context_str}\n\nMENSAJE DEL CLIENTE: {message}\n\nRESPUESTA:"
        
        # Generar respuesta según el modelo configurado
        if self.model == 'ollama':
            response = self._generate_with_ollama(full_prompt)
        elif self.model == 'gemini':
            response = self._generate_with_gemini(full_prompt)
        else:
            response = self._generate_rule_based(message, context)
        
        # Guardar respuesta en historial
        self.conversation_history[client_id].append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().isoformat()
        })
        
        return response
    
    def _generate_with_ollama(self, prompt):
        """Genera respuesta usando Ollama (modelo local)"""
        try:
            import ollama
            
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            return response['message']['content'].strip()
        except Exception as e:
            print(f"Error con Ollama: {e}")
            return self._generate_rule_based(prompt, {})
    
    def _generate_with_gemini(self, prompt):
        """Genera respuesta usando Google Gemini (capa gratuita)"""
        try:
            import google.generativeai as genai
            
            # Configurar API Key (debe estar en variables de entorno)
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            
            return response.text.strip()
        except Exception as e:
            print(f"Error con Gemini: {e}")
            return self._generate_rule_based(prompt, {})
    
    def _generate_rule_based(self, message, context):
        """
        Genera respuestas basadas en reglas (fallback si no hay IA)
        Útil para testing o cuando los modelos no están disponibles
        """
        message_lower = message.lower()
        
        # Saludos
        if any(word in message_lower for word in ['hola', 'buenas', 'qué tal', 'buen día']):
            return "¡Hola! 👋 Bienvenido a MaccielBarber 💈. Soy el asistente virtual. ¿En qué puedo ayudarte hoy? Puedo agendarte un turno, ver horarios disponibles o decirte si el barbero está libre. ✂️"
        
        # Consulta de estado
        if any(word in message_lower for word in ['está', 'ocupado', 'libre', 'cortando', 'disponible']):
            if context.get('current_status'):
                status = context['current_status']
                if status.get('busy'):
                    return f"El barbero está en medio de un corte ahora mismo 💈. Termina aproximadamente a las {status['current_event']['end']}. ¿Querés esperar o preferís agendar para más tarde? 📅"
                else:
                    return "¡El barbero está disponible ahora mismo! 💈✂️ ¿Querés venir ya o preferís agendar para otro horario?"
            return "Déjame verificar el estado actual... Un momento por favor."
        
        # Agendar turno
        if any(word in message_lower for word in ['agendar', 'reservar', 'turno', 'cita', 'quiero']):
            booking_info = self.extract_booking_info(message)
            
            if booking_info:
                return f"¡Perfecto! 🎯 Tengo estos datos:\n- Cliente: {booking_info['nombre']}\n- Servicio: {booking_info['servicio']}\n- Fecha: {booking_info['fecha']}\n- Hora: {booking_info['hora']}\n\nVoy a verificar disponibilidad..."
            
            # Si falta información, pedirla
            missing = []
            if not any(word in message_lower for word in ['me llamo', 'mi nombre', 'soy']):
                missing.append("tu nombre")
            if not any(word in message_lower for word in ['corte', 'barba', 'combo']):
                missing.append("qué servicio querés (Corte, Barba o Combo)")
            if not any(char.isdigit() for char in message) or not any(word in message_lower for word in ['hoy', 'mañana', '/', '-']):
                missing.append("la fecha")
            if not any(char.isdigit() for char in message) or not any(word in message_lower for word in ['hs', ':', 'a las']):
                missing.append("la hora")
            
            if missing:
                return f"Para agendar tu turno necesito que me digas: {', '.join(missing)}. Por favor, dame esos datos. 💈"
        
        # Horarios
        if any(word in message_lower for word in ['horario', 'disponibilidad', 'turnos', 'huecos']):
            if context.get('available_hours'):
                hours = self.get_available_hours_format(context['available_hours'])
                return f"Estos son los horarios disponibles: {hours}. ¿Cuál te conviene? 📅"
            return "¿Para qué fecha querés ver los horarios disponibles? Puedo mostrarte los turnos libres. 📅"
        
        # Servicios y precios
        if any(word in message_lower for word in ['precio', 'valor', 'cuánto', 'servicios']):
            return "Nuestros servicios:\n✂️ Corte de cabello (30 min) - $5000\n🧔 Barba (20 min) - $3000\n🎯 Combo Corte + Barba (45 min) - $7000\n\n¿Cuál te gustaría agendar?"
        
        # Despedidas
        if any(word in message_lower for word in ['gracias', 'chau', 'adiós', 'hasta luego']):
            return "¡Gracias a vos! 💈 Cualquier cosa estoy acá para ayudarte. ¡Te esperamos en MaccielBarber! ✂️"
        
        # Default
        return "Entiendo. Para ayudarte mejor, ¿podrías decirme si querés agendar un turno, ver horarios disponibles o saber si el barbero está libre? 💈"
    
    def clear_conversation(self, client_id):
        """Limpia el historial de conversación de un cliente"""
        if client_id in self.conversation_history:
            del self.conversation_history[client_id]
