#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import time
import threading
import queue
import requests
import pyttsx3
import speech_recognition as sr

class AIAssistant:
    """Asistente de IA con capacidad de voz usando AI Studio."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.logger = logging.getLogger('AIAssistant')
        
        # Configuración de AI Studio
        self.api_key = self.config.get('ai_studio_api_key', '')
        self.api_url = self.config.get('ai_studio_url', 'https://api.aistudio.com/v1/chat/completions')
        self.model = self.config.get('ai_studio_model', 'gpt-4')
        
        # Inicializar motor de voz
        self.engine = pyttsx3.init()
        self.configure_voice()
        
        # Reconocimiento de voz
        self.recognizer = sr.Recognizer()
        
        # Cola de mensajes para hablar
        self.speech_queue = queue.Queue()
        self.speaking_thread = None
        self.running = False
        
        # Historial de conversación
        self.conversation_history = []
        self.max_history = self.config.get('max_history', 10)
        
        # Callbacks
        self.command_callbacks = {}
        
        if not self.api_key:
            self.logger.warning("No se ha configurado API key para AI Studio")
            
    def configure_voice(self):
        """Configura el motor de voz."""
        try:
            # Ajustar velocidad
            self.engine.setProperty('rate', self.config.get('voice_rate', 150))
            
            # Ajustar volumen
            self.engine.setProperty('volume', self.config.get('voice_volume', 0.8))
            
            # Seleccionar voz en español si está disponible
            voices = self.engine.getProperty('voices')
            selected_voice = None
            
            # Buscar voz en español
            for voice in voices:
                if 'spanish' in voice.id.lower() or 'es' in voice.id.lower():
                    selected_voice = voice.id
                    break
            
            # Si no se encuentra, usar la primera disponible
            if not selected_voice and voices:
                selected_voice = voices[0].id
                
            if selected_voice:
                self.engine.setProperty('voice', selected_voice)
                self.logger.info(f"Voz configurada: {selected_voice}")
        except Exception as e:
            self.logger.error(f"Error al configurar voz: {str(e)}")
            
    def start(self):
        """Inicia el asistente."""
        if self.running:
            return
            
        self.running = True
        self.speaking_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.speaking_thread.start()
        self.logger.info("Asistente de IA iniciado")
        
    def stop(self):
        """Detiene el asistente."""
        self.running = False
        if self.speaking_thread:
            self.speech_queue.put(None)  # Señal para detener el hilo
            self.speaking_thread.join(timeout=2)
            self.speaking_thread = None
        self.logger.info("Asistente de IA detenido")
        
    def _speech_worker(self):
        """Hilo trabajador para síntesis de voz."""
        while self.running:
            try:
                text = self.speech_queue.get(timeout=1)
                if text is None:
                    break
                    
                self.logger.info(f"Hablando: {text}")
                self.engine.say(text)
                self.engine.runAndWait()
                self.speech_queue.task_done()
            except queue.Empty:
                pass
            except Exception as e:
                self.logger.error(f"Error en síntesis de voz: {str(e)}")
                time.sleep(1)
                
    def say(self, text):
        """Añade texto a la cola para ser hablado."""
        if not text or not isinstance(text, str):
            return
            
        self.speech_queue.put(text)
        
    def listen(self, timeout=5):
        """Escucha y reconoce el habla."""
        text = ""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                self.logger.info("Escuchando...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                
            self.logger.info("Reconociendo...")
            text = self.recognizer.recognize_google(audio, language="es-ES")
            self.logger.info(f"Reconocido: {text}")
        except sr.WaitTimeoutError:
            self.logger.info("Timeout esperando audio")
        except sr.UnknownValueError:
            self.logger.info("No se pudo reconocer el audio")
        except sr.RequestError as e:
            self.logger.error(f"Error en API de reconocimiento: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error al escuchar: {str(e)}")
            
        return text
        
    def process_with_ai_studio(self, user_message):
        """Procesa un mensaje con AI Studio."""
        if not self.api_key:
            return "Error: API key de AI Studio no configurada"
            
        try:
            # Preparar historial de conversación
            messages = [
                {"role": "system", "content": [
                    {"type": "text", "text": "Eres un asistente virtual para un sistema domótico. Responde de manera útil, precisa y breve en español."}
                ]}
            ]
            
            # Añadir historial de conversación
            for msg in self.conversation_history:
                messages.append(msg)
            
            # Añadir mensaje actual
            messages.append({
                "role": "user",
                "content": [{"type": "text", "text": user_message}]
            })
            
            # Preparar payload
            payload = {
                "model": self.model,
                "messages": messages
            }
            
            # Headers
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Realizar solicitud
            response = requests.post(self.api_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                response_data = response.json()
                ai_message = response_data["choices"][0]["message"]["content"][0]["text"]
                
                # Actualizar historial
                self.conversation_history.append({"role": "user", "content": [{"type": "text", "text": user_message}]})
                self.conversation_history.append({"role": "assistant", "content": [{"type": "text", "text": ai_message}]})
                
                # Mantener tamaño del historial
                while len(self.conversation_history) > self.max_history:
                    self.conversation_history.pop(0)
                    
                return ai_message
            else:
                error_msg = f"Error en API (código {response.status_code}): {response.text}"
                self.logger.error(error_msg)
                return f"Error al comunicarse con AI Studio: {response.status_code}"
        except Exception as e:
            self.logger.error(f"Error al procesar con AI Studio: {str(e)}")
            return f"Error al procesar con IA: {str(e)}"
            
    def register_command(self, command_name, callback):
        """Registra un callback para un comando específico."""
        self.command_callbacks[command_name.lower()] = callback
        self.logger.info(f"Comando registrado: {command_name}")
        
    def process_command(self, text):
        """Procesa un texto para detectar y ejecutar comandos."""
        text = text.lower()
        
        # Primero buscar comandos directos
        for command_name, callback in self.command_callbacks.items():
            if command_name in text:
                self.logger.info(f"Comando detectado: {command_name}")
                return callback(text)
        
        # Si no hay comandos directos, procesar con IA
        response = self.process_with_ai_studio(text)
        self.say(response)
        return response