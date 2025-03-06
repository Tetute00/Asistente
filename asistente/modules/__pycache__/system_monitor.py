#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import psutil
import platform
import logging
import time
import threading

class SystemMonitor:
    """Monitor de recursos del sistema."""
    
    def __init__(self):
        self.logger = logging.getLogger('SystemMonitor')
        self.running = False
        self.data = {
            'battery': {'percent': 0, 'charging': False, 'time_left': 'Unknown'},
            'cpu': {'percent': 0, 'temperature': 'N/A'},
            'memory': {'percent': 0, 'used': 0, 'total': 0},
            'system_info': self._get_system_info()
        }
        self.update_thread = None
        
    def _get_system_info(self):
        """Obtiene información estática del sistema."""
        try:
            return {
                'os': platform.system(),
                'os_version': platform.release(),
                'hostname': platform.node(),
                'processor': platform.processor(),
                'python_version': platform.python_version()
            }
        except Exception as e:
            self.logger.error(f"Error al obtener información del sistema: {str(e)}")
            return {}
            
    def _get_battery_info(self):
        """Obtiene información de la batería."""
        try:
            if not hasattr(psutil, "sensors_battery"):
                return {'percent': 0, 'charging': False, 'time_left': 'Not supported'}
                
            battery = psutil.sensors_battery()
            if battery:
                time_left = ""
                if battery.power_plugged:
                    if battery.percent < 100:
                        time_left = "Cargando"
                    else:
                        time_left = "Cargado"
                elif battery.secsleft > 0:
                    hours, remainder = divmod(battery.secsleft, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    time_left = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
                else:
                    time_left = "Desconocido"
                    
                return {
                    'percent': battery.percent,
                    'charging': battery.power_plugged,
                    'time_left': time_left
                }
            else:
                return {'percent': 0, 'charging': False, 'time_left': 'Not available'}
        except Exception as e:
            self.logger.error(f"Error al obtener información de batería: {str(e)}")
            return {'percent': 0, 'charging': False, 'time_left': f'Error: {str(e)}'}
            
    def _get_cpu_info(self):
        """Obtiene información de CPU."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Intentar obtener temperatura (no disponible en todos los sistemas)
            temperature = 'N/A'
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        for entry in entries:
                            temperature = f"{entry.current}°C"
                            break
                        if temperature != 'N/A':
                            break
                            
            return {'percent': cpu_percent, 'temperature': temperature}
        except Exception as e:
            self.logger.error(f"Error al obtener información de CPU: {str(e)}")
            return {'percent': 0, 'temperature': 'Error'}
            
    def _get_memory_info(self):
        """Obtiene información de memoria."""
        try:
            memory = psutil.virtual_memory()
            return {
                'percent': memory.percent,
                'used': memory.used / (1024 * 1024),  # MB
                'total': memory.total / (1024 * 1024)  # MB
            }
        except Exception as e:
            self.logger.error(f"Error al obtener información de memoria: {str(e)}")
            return {'percent': 0, 'used': 0, 'total': 0}
            
    def update_data(self):
        """Actualiza todos los datos del sistema."""
        self.data['battery'] = self._get_battery_info()
        self.data['cpu'] = self._get_cpu_info()
        self.data['memory'] = self._get_memory_info()
        
    def _update_loop(self):
        """Bucle de actualización periódica."""
        while self.running:
            try:
                self.update_data()
                time.sleep(5)  # Actualizar cada 5 segundos
            except Exception as e:
                self.logger.error(f"Error en bucle de actualización: {str(e)}")
                time.sleep(10)  # Esperar más en caso de error
                
    def start_monitoring(self):
        """Inicia el monitoreo del sistema."""
        if self.running:
            return
            
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        self.logger.info("Monitor de sistema iniciado")
        
    def stop_monitoring(self):
        """Detiene el monitoreo del sistema."""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=2)
            self.update_thread = None
        self.logger.info("Monitor de sistema detenido")
        
    def get_data(self):
        """Obtiene los datos actuales del sistema."""
        if not self.running:
            self.update_data()  # Actualizar una vez si no está en monitoreo continuo
        return self.data