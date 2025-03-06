#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import requests
import subprocess
import socket
import platform
import threading
import time
from flask import jsonify

class RemoteControl:
    """Controlador para comunicación remota entre dispositivos."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.logger = logging.getLogger('RemoteControl')
        self.remote_devices = self.config.get('remote_devices', {})
        self.device_status = {}  # Estado de conectividad de los dispositivos
        self.polling_thread = None
        self.running = False
        
    def start_polling(self):
        """Inicia el sondeo de dispositivos remotos."""
        if self.running:
            return
            
        self.running = True
        self.polling_thread = threading.Thread(target=self._poll_devices, daemon=True)
        self.polling_thread.start()
        self.logger.info("Sondeo de dispositivos remotos iniciado")
        
    def stop_polling(self):
        """Detiene el sondeo de dispositivos remotos."""
        self.running = False
        if self.polling_thread:
            self.polling_thread.join(timeout=2)
            self.polling_thread = None
        self.logger.info("Sondeo de dispositivos remotos detenido")
        
    def _poll_devices(self):
        """Función de sondeo periódico de dispositivos."""
        while self.running:
            for device_name, device_info in self.remote_devices.items():
                try:
                    ip = device_info.get('ip', '')
                    port = device_info.get('port', 80)
                    
                    # Comprobar si el dispositivo responde
                    if device_info.get('type') == 'api':
                        # Verificar API
                        url = f"http://{ip}:{port}/api/status"
                        response = requests.get(url, timeout=2)
                        self.device_status[device_name] = {
                            'online': response.status_code == 200,
                            'last_check': time.time(),
                            'info': response.json() if response.status_code == 200 else {}
                        }
                    else:
                        # Comprobar ping básico
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(2)
                        result = sock.connect_ex((ip, port))
                        sock.close()
                        
                        self.device_status[device_name] = {
                            'online': result == 0,
                            'last_check': time.time()
                        }
                except Exception as e:
                    self.logger.warning(f"Error al comprobar dispositivo {device_name}: {str(e)}")
                    self.device_status[device_name] = {
                        'online': False,
                        'last_check': time.time(),
                        'error': str(e)
                    }
            
            # Esperar antes de la siguiente comprobación
            time.sleep(30)  # Comprobar cada 30 segundos
    
    def execute_local_command(self, command):
        """Ejecuta un comando en el sistema local."""
        try:
            # Lista de comandos permitidos para seguridad
            allowed_commands = {
                'system_info': ['uname -a'],
                'ip_info': ['ip addr', 'ifconfig'],
                'memory_info': ['free -h'],
                'disk_info': ['df -h'],
                'process_list': ['ps aux | head -10'],
                'network_test': ['ping -c 4 google.com'],
                'custom': []  # Se llenará con comandos personalizados desde configuración
            }
            
            # Añadir comandos personalizados si están configurados
            if 'allowed_commands' in self.config:
                allowed_commands['custom'] = self.config['allowed_commands']
            
            # Verificar si el comando está permitido
            command_allowed = False
            for cmd_category, cmd_list in allowed_commands.items():
                for allowed_cmd in cmd_list:
                    if command.strip() == allowed_cmd or command.startswith(allowed_cmd + ' '):
                        command_allowed = True
                        break
                if command_allowed:
                    break
            
            if not command_allowed:
                return {
                    'success': False,
                    'output': 'Comando no permitido por razones de seguridad',
                    'error': 'Unauthorized command'
                }
            
            # Ejecutar comando
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr,
                'code': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': 'Comando excedió el tiempo límite de ejecución',
                'code': -1
            }
        except Exception as e:
            self.logger.error(f"Error al ejecutar comando: {str(e)}")
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'code': -1
            }
    
    def execute_remote_command(self, device_name, command, command_type='shell'):
        """Ejecuta un comando en un dispositivo remoto."""
        if device_name not in self.remote_devices:
            return {
                'success': False,
                'error': f"Dispositivo '{device_name}' no encontrado"
            }
            
        device = self.remote_devices[device_name]
        
        try:
            url = f"http://{device['ip']}:{device['port']}/api/execute"
            
            payload = {
                'command': command,
                'type': command_type,
                'token': device.get('token', '')  # Token de autenticación si es necesario
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f"Error en API remota: {response.status_code}",
                    'response': response.text
                }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': "Tiempo de espera agotado"
            }
        except Exception as e:
            self.logger.error(f"Error al ejecutar comando remoto: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_device_status(self):
        """Obtiene el estado de todos los dispositivos."""
        return self.device_status
        
    def add_device(self, name, ip, port, device_type='api', token=''):
        """Añade un nuevo dispositivo remoto."""
        self.remote_devices[name] = {
            'ip': ip,
            'port': port,
            'type': device_type,
            'token': token
        }
        
        # Guardar configuración actualizada
        self.save_config()
        return True
        
    def remove_device(self, name):
        """Elimina un dispositivo remoto."""
        if name in self.remote_devices:
            del self.remote_devices[name]
            if name in self.device_status:
                del self.device_status[name]
                
            # Guardar configuración actualizada
            self.save_config()
            return True
        return False
        
    def save_config(self):
        """Guarda la configuración actualizada."""
        try:
            # Actualizar configuración en memoria
            self.config['remote_devices'] = self.remote_devices
            
            # El guardado real lo debe hacer el sistema principal que gestiona la configuración
            return True
        except Exception as e:
            self.logger.error(f"Error al guardar configuración: {str(e)}")
            return False