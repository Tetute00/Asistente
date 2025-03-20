"""
Gestor de conexiones WebSocket para JARVIS
Maneja las conexiones de clientes y eventos
"""
from flask_socketio import emit, join_room, leave_room
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self, socketio):
        """Inicializa el gestor con la instancia de SocketIO"""
        self.socketio = socketio
        self.clients = {}  # Registra conexiones
        self.setup_events()
        logger.info("WebSocketManager inicializado")
    
    def setup_events(self):
        """Configura los manejadores de eventos para WebSocket"""
        @self.socketio.on('connect')
        def handle_connect():
            client_id = self._get_client_id()
            self.clients[client_id] = {
                'id': client_id,
                'type': 'web',  # De donde esta entrando el cliente "Web;Kali;Win"
                'connected_at': self._get_timestamp()
            }
            join_room(client_id)  # Hace la sala
            logger.info(f"Cliente conectado: {client_id}")
            emit('connected', {'client_id': client_id})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            client_id = self._get_client_id()
            if client_id in self.clients:
                del self.clients[client_id]
                logger.info(f"Cliente desconectado: {client_id}")
        
        @self.socketio.on('register_client')
        def handle_register(data):
            """Registra un cliente con información adicional"""
            client_id = self._get_client_id()
            client_type = data.get('type', 'web')
            client_name = data.get('name', f"Cliente {client_id[:8]}")
            
            if client_id in self.clients:
                self.clients[client_id].update({
                    'type': client_type,
                    'name': client_name,
                    'info': data.get('info', {})
                })
                
                # Correcto o no
                emit('client_registered', {
                    'client_id': client_id,
                    'type': client_type,
                    'name': client_name
                })
                
                # Notificacion de nuevo cliente
                if client_type in ['windows', 'kali']:
                    self.broadcast_system_event('system_connected', {
                        'client_id': client_id,
                        'type': client_type,
                        'name': client_name
                    })
                
                logger.info(f"Cliente registrado: {client_name} ({client_type})")
        
        @self.socketio.on('system_update')
        def handle_system_update(data):
            """Maneja actualizaciones del estado del sistema"""
            client_id = self._get_client_id()
            if client_id in self.clients:
                # Recargar informacion
                if 'system_info' in data:
                    if 'info' not in self.clients[client_id]:
                        self.clients[client_id]['info'] = {}
                    self.clients[client_id]['info'].update(data['system_info'])
                
                # Actualiza todos los clientes
                self.broadcast_to_web('system_update', data)
                logger.debug(f"Actualización del sistema recibida: {client_id}")
        
        # === Comandos === 
        
        @self.socketio.on('execute_command')
        def handle_execute_command(data):
            """Maneja solicitudes para ejecutar comandos en un sistema"""
            target_id = data.get('target_id')
            command = data.get('command')
            params = data.get('params', {})
            
            logger.info(f"Solicitud de comando: {command} en {target_id}")
            
            # Testeo
            if not target_id or not command:
                emit('command_response', {
                    'success': False,
                    'error': 'Falta ID de destino o comando'
                })
                return
            
            # Verificar si el cliente destino existe
            if target_id not in self.clients:
                emit('command_response', {
                    'success': False,
                    'error': 'Sistema destino no conectado'
                })
                return
            
            # Reenviar comando al cliente destino
            self.send_to_client(target_id, 'command', {
                'command': command,
                'params': params,
                'request_id': data.get('request_id')
            })
            
            # Confirmar que el comando fue enviado
            emit('command_sent', {
                'target_id': target_id,
                'request_id': data.get('request_id')
            })
        
        @self.socketio.on('command_result')
        def handle_command_result(data):
            """Maneja resultados de comandos ejecutados por clientes"""
            request_id = data.get('request_id')
            success = data.get('success', False)
            result = data.get('result')
            error = data.get('error')
            
            logger.debug(f"Resultado de comando recibido: {request_id}, éxito: {success}")
            
            # Enviar el resultado a los clientes
            # Mostrar resultado del comando
            self.broadcast_to_web('command_result', {
                'request_id': request_id,
                'success': success,
                'result': result,
                'error': error
            })
    
    def broadcast_to_web(self, event, data):
        """Emite un evento a todos los clientes web"""
        for client_id, client in self.clients.items():
            if client.get('type') == 'web':
                self.socketio.emit(event, data, room=client_id)
    
    def broadcast_system_event(self, event, data):
        """Emite un evento de sistema a todos los clientes"""
        self.socketio.emit(event, data)
    
    def send_to_client(self, client_id, event, data):
        """Envía un evento a un cliente específico"""
        self.socketio.emit(event, data, room=client_id)
    
    def _get_client_id(self):
        """Obtiene el ID del cliente actual"""
        from flask import request
        return request.sid
    
    def _get_timestamp(self):
        """Obtiene la marca de tiempo actual"""
        from datetime import datetime
        return datetime.utcnow().isoformat()