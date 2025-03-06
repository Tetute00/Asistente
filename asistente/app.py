#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import threading
import signal
import sys
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response, send_from_directory

# Importar módulos del sistema
from modules.system_monitor import SystemMonitor
from modules.auth_manager import AuthManager
from modules.ai_assistant import AIAssistant
from modules.remote_control import RemoteControl

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('domotica.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Domotica')

class DomoticaApp:
    """Aplicación principal de domótica."""
    
    def __init__(self):
        self.logger = logger
        self.config = self._load_config()
        
        # Inicializar Flask
        self.app = Flask(__name__,
                        static_folder='web_interface/static',
                        template_folder='web_interface/templates')
        
        # Inicializar componentes
        self.system_monitor = SystemMonitor()
        self.auth_manager = AuthManager()
        self.ai_assistant = AIAssistant(self.config.get('voice_assistant', {}))
        self.remote_control = RemoteControl(self.config.get('remote_control', {}))
        
        # Configurar rutas de la aplicación
        self._setup_routes()
        
        # Estado de la aplicación
        self.running = False
        
    def _load_config(self):
        """Carga la configuración desde archivos JSON."""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
            else:
                self.logger.warning(f"Archivo de configuración {config_path} no encontrado. Usando valores por defecto.")
                return self._create_default_config()
        except Exception as e:
            self.logger.error(f"Error al cargar configuración: {e}")
            return self._create_default_config()
    
    def _create_default_config(self):
        """Crea una configuración por defecto."""
        default_config = {
            "web_server": {
                "host": "0.0.0.0",
                "port": 8080,
                "debug": False
            },
            "voice_assistant": {
                "ai_studio_api_key": "",
                "voice_rate": 150,
                "voice_volume": 0.8,
                "wake_word": "casa"
            },
            "remote_control": {
                "remote_devices": {},
                "allowed_commands": []
            }
        }
        
        # Guardar configuración por defecto
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error al guardar configuración por defecto: {e}")
            
        return default_config
        
    def _setup_routes(self):
        """Configura las rutas de la aplicación Flask."""
        
        # Rutas para la interfaz web
        @self.app.route('/')
        def index():
            return render_template('index.html')
            
        @self.app.route('/<path:path>')
        def static_files(path):
            return send_from_directory('web_interface', path)
            
        # API: Autenticación
        @self.app.route('/api/auth/login', methods=['POST'])
        def auth_login():
            data = request.json
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return jsonify({"success": False, "message": "Usuario y contraseña requeridos"})
                
            # Si no hay usuarios, crear admin por defecto
            if not self.auth_manager.users:
                self.auth_manager.add_user('admin', 'admin', 'admin')
                self.logger.info("Usuario admin creado con contraseña por defecto")
                
            success, result = self.auth_manager.authenticate(username, password)
            
            if success:
                return jsonify({"success": True, "token": result})
            else:
                return jsonify({"success": False, "message": result})
                
        @self.app.route('/api/auth/verify')
        def auth_verify():
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            
            if not token:
                return jsonify({"valid": False})
                
            success, session = self.auth_manager.verify_session(token)
            
            if success:
                return jsonify({"valid": True, "username": session['username'], "role": session['role']})
            else:
                return jsonify({"valid": False})
                
        @self.app.route('/api/auth/logout', methods=['POST'])
        def auth_logout():
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            
            if not token:
                return jsonify({"success": False})
                
            success = self.auth_manager.logout(token)
            return jsonify({"success": success})
            
        # API: Sistema
        @self.app.route('/api/system/status')
        def system_status():
            # Verificar autenticación
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if token and not self.auth_manager.verify_session(token)[0]:
                return jsonify({"error": "No autorizado"}), 401
                
            return jsonify(self.system_monitor.get_data())
            
        @self.app.route('/api/system/detailed')
        def system_detailed():
            # Verificar autenticación
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if token and not self.auth_manager.verify_session(token)[0]:
                return jsonify({"error": "No autorizado"}), 401
            
            # Obtener datos básicos
            data = self.system_monitor.get_data()
            
            # Añadir datos adicionales
            uptime = os.popen('uptime -p').read().strip()
            data['uptime'] = uptime
            
            # Añadir historial simulado para gráficos
            import random
            history = {
                "labels": [f"{i}:00" for i in range(12)],
                "cpu": [random.randint(10, 90) for _ in range(12)],
                "memory": [random.randint(30, 70) for _ in range(12)],
                "batteryLabels": [f"{i}:00" for i in range(24)],
                "battery": [random.randint(60, 95) for _ in range(24)]
            }
            
            data['history'] = history
            
            return jsonify(data)
            
        @self.app.route('/api/system/execute', methods=['POST'])
        def system_execute():
            # Verificar autenticación
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if token and not self.auth_manager.verify_session(token)[0]:
                return jsonify({"success": False, "error": "No autorizado"}), 401
                
            data = request.json
            command = data.get('command')
            
            if not command:
                return jsonify({"success": False, "error": "Comando requerido"})
                
            result = self.remote_control.execute_local_command(command)
            return jsonify(result)
        
        # API: Control Remoto
        @self.app.route('/api/remote/devices')
        def remote_devices():
            # Verificar autenticación
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if token and not self.auth_manager.verify_session(token)[0]:
                return jsonify({"error": "No autorizado"}), 401
                
            devices = []
            for name, device in self.remote_control.remote_devices.items():
                status = self.remote_control.device_status.get(name, {'online': False})
                devices.append({
                    'name': name,
                    'ip': device['ip'],
                    'port': device['port'],
                    'online': status.get('online', False)
                })
                
            return jsonify({"devices": devices})
            
        @self.app.route('/api/remote/device', methods=['POST'])
        def add_device():
            # Verificar autenticación
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if token and not self.auth_manager.verify_session(token)[0]:
                return jsonify({"success": False, "error": "No autorizado"}), 401
                
            data = request.json
            name = data.get('name')
            ip = data.get('ip')
            port = data.get('port')
            device_type = data.get('type', 'api')
            token = data.get('token', '')
            
            if not name or not ip or not port:
                return jsonify({"success": False, "message": "Datos incompletos"})
                
            success = self.remote_control.add_device(name, ip, port, device_type, token)
            return jsonify({"success": success})
            
        @self.app.route('/api/remote/device/<name>', methods=['DELETE'])
        def remove_device(name):
            # Verificar autenticación
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if token and not self.auth_manager.verify_session(token)[0]:
                return jsonify({"success": False, "error": "No autorizado"}), 401
                
            success = self.remote_control.remove_device(name)
            return jsonify({"success": success})
            
        @self.app.route('/api/remote/execute', methods=['POST'])
        def remote_execute():
            # Verificar autenticación
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if token and not self.auth_manager.verify_session(token)[0]:
                return jsonify({"success": False, "error": "No autorizado"}), 401
                
            data = request.json
            device = data.get('device')
            command = data.get('command')
            command_type = data.get('type', 'shell')
            
            if not device or not command:
                return jsonify({"success": False, "error": "Datos incompletos"})
                
            result = self.remote_control.execute_remote_command(device, command, command_type)
            return jsonify(result)
            
        # API: Asistente de Voz
        @self.app.route('/api/voice/process', methods=['POST'])
        def voice_process():
            # Verificar autenticación
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if token and not self.auth_manager.verify_session(token)[0]:
                return jsonify({"success": False, "error": "No autorizado"}), 401
                
            data = request.json
            text = data.get('text')
            
            if not text:
                return jsonify({"success": False, "error": "Texto requerido"})
                
            response = self.ai_assistant.process_with_ai_studio(text)
            
            # Hablar respuesta si está configurado
            if self.config.get('voice_assistant', {}).get('auto_speak', True):
                self.ai_assistant.say(response)
                
            return jsonify({"success": True, "response": response})
            
        @self.app.route('/api/voice/listen', methods=['POST'])
        def voice_listen():
            # Verificar autenticación
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if token and not self.auth_manager.verify_session(token)[0]:
                return jsonify({"success": False, "error": "No autorizado"}), 401
                
            # Iniciar escucha en un hilo separado
            def listen_thread():
                text = self.ai_assistant.listen()
                if text:
                    response = self.ai_assistant.process_with_ai_studio(text)
                    self.ai_assistant.say(response)
            
            threading.Thread(target=listen_thread, daemon=True).start()
            return jsonify({"success": True})
            
        @self.app.route('/api/voice/stop', methods=['POST'])
        def voice_stop():
            # No necesita verificación de autenticación ya que es para detener
            # TODO: Implementar detención de escucha
            return jsonify({"success": True})
            
        @self.app.route('/api/voice/results')
        def voice_results():
            # Verificar autenticación
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if token and not self.auth_manager.verify_session(token)[0]:
                return jsonify({"error": "No autorizado"}), 401
                
            # En una implementación completa, aquí se retornarían
            # los resultados reales del reconocimiento de voz
            return jsonify({"listening": False})
            
        @self.app.route('/api/voice/test', methods=['POST'])
        def voice_test():
            # Verificar autenticación
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if token and not self.auth_manager.verify_session(token)[0]:
                return jsonify({"success": False, "error": "No autorizado"}), 401
                
            data = request.json
            rate = data.get('rate', 150)
            volume = data.get('volume', 0.8)
            text = data.get('text', 'Prueba de voz del asistente')
            
            # Configurar voz según parámetros
            self.ai_assistant.engine.setProperty('rate', int(rate))
            self.ai_assistant.engine.setProperty('volume', float(volume))
            
            # Hablar texto de prueba
            self.ai_assistant.say(text)
            
            return jsonify({"success": True})
            
        # API: Configuración
        @self.app.route('/api/settings')
        def get_settings():
            # Verificar autenticación
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if token and not self.auth_manager.verify_session(token)[0]:
                return jsonify({"error": "No autorizado"}), 401
                
            # Retornar configuración (sin valores sensibles)
            safe_config = {
                'voice': {
                    'rate': self.config.get('voice_assistant', {}).get('voice_rate', 150),
                    'volume': self.config.get('voice_assistant', {}).get('voice_volume', 0.8),
                    'wake_word': self.config.get('voice_assistant', {}).get('wake_word', 'casa')
                },
                'system': {
                    'refresh_interval': self.config.get('web_server', {}).get('refresh_interval', 10),
                    'theme': self.config.get('web_server', {}).get('theme', 'auto'),
                    'auto_start': self.config.get('web_server', {}).get('auto_start', True),
                    'log_activity': self.config.get('web_server', {}).get('log_activity', True),
                    'notifications': self.config.get('web_server', {}).get('notifications', True)
                }
            }
            
            return jsonify(safe_config)
            
        @self.app.route('/api/settings', methods=['POST'])
        def save_settings():
            # Verificar autenticación
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if token and not self.auth_manager.verify_session(token)[0]:
                return jsonify({"success": False, "error": "No autorizado"}), 401
                
            data = request.json
            
            # Actualizar configuración
            if 'voice' in data:
                if 'voice_assistant' not in self.config:
                    self.config['voice_assistant'] = {}
                    
                self.config['voice_assistant']['voice_rate'] = data['voice'].get('rate', 150)
                self.config['voice_assistant']['voice_volume'] = data['voice'].get('volume', 0.8)
                self.config['voice_assistant']['wake_word'] = data['voice'].get('wake_word', 'casa')
                
            if 'system' in data:
                if 'web_server' not in self.config:
                    self.config['web_server'] = {}
                    
                self.config['web_server']['refresh_interval'] = data['system'].get('refresh_interval', 10)
                self.config['web_server']['theme'] = data['system'].get('theme', 'auto')
                self.config['web_server']['auto_start'] = data['system'].get('auto_start', True)
                self.config['web_server']['log_activity'] = data['system'].get('log_activity', True)
                self.config['web_server']['notifications'] = data['system'].get('notifications', True)
                
            # Guardar configuración
            try:
                config_path = os.path.join(os.path.dirname(__file__), 'config.json')
                with open(config_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
                    
                return jsonify({"success": True})
            except Exception as e:
                self.logger.error(f"Error al guardar configuración: {e}")
                return jsonify({"success": False, "message": f"Error al guardar: {str(e)}"})
    
    def start(self):
        """Inicia la aplicación."""
        self.logger.info("Iniciando aplicación de domótica")
        self.running = True
        
        # Iniciar monitoreo del sistema
        self.system_monitor.start_monitoring()
        
        # Iniciar asistente de voz
        self.ai_assistant.start()
        
        # Iniciar monitoreo de dispositivos remotos
        self.remote_control.start_polling()
        
        # Iniciar servidor web
        host = self.config.get('web_server', {}).get('host', '0.0.0.0')
        port = self.config.get('web_server', {}).get('port', 8080)
        debug = self.config.get('web_server', {}).get('debug', False)
        
        self.logger.info(f"Iniciando servidor web en {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)
        
    def stop(self):
        """Detiene la aplicación."""
        if not self.running:
            return
            
        self.logger.info("Deteniendo aplicación de domótica")
        self.running = False
        
        # Detener componentes
        self.system_monitor.stop_monitoring()
        self.ai_assistant.stop()
        self.remote_control.stop_polling()
        
        self.logger.info("Aplicación detenida")


# Manejador de señales para cierre limpio
def signal_handler(sig, frame):
    print('\nInterrupción recibida. Deteniendo aplicación...')
    if 'app_instance' in globals():
        app_instance.stop()
    sys.exit(0)

# Registrar manejadores de señal
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    app_instance = DomoticaApp()
    app_instance.start()