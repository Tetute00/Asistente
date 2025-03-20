/**
 * Cliente WebSocket para JARVIS
 * Comunicacion server cliente
 */
class WebSocketClient {
    constructor(serverUrl) {
        this.serverUrl = serverUrl || 'http://localhost:5000';
        this.socket = null;
        this.connected = false;
        this.clientId = null;
        this.eventHandlers = {};
        
        // Vincular métodos
        this.connect = this.connect.bind(this);
        this.disconnect = this.disconnect.bind(this);
        this.on = this.on.bind(this);
        this.off = this.off.bind(this);
        this.emit = this.emit.bind(this);
    }
    
    /**
     * Conecta con el servidor 
     */
    connect() {
        // Importacion de Socket.IO
        if (typeof io === 'undefined') {
            console.error('Socket.IO no está definido. ¿Has incluido la biblioteca?');
            return;
        }
        
        console.log(`Conectando a WebSocket: ${this.serverUrl}`);
        this.socket = io(this.serverUrl);
        
        this.socket.on('connect', () => {
            this.connected = true;
            console.log('Conectado al servidor WebSocket');
            
            this.emit('register_client', {
                type: 'web',
                name: 'JARVIS Web Interface',
                info: {
                    userAgent: navigator.userAgent
                }
            });
            
            if (this.eventHandlers['connect']) {
                this.eventHandlers['connect'].forEach(handler => handler());
            }
        });
        
        this.socket.on('connected', (data) => {
            this.clientId = data.client_id;
            console.log(`ID de cliente asignado: ${this.clientId}`);
        });
        
        this.socket.on('disconnect', () => {
            this.connected = false;
            console.log('Desconectado del servidor WebSocket');
            
            if (this.eventHandlers['disconnect']) {
                this.eventHandlers['disconnect'].forEach(handler => handler());
            }
        });
        
        // Notificar de error de conexion
        this.socket.on('connect_error', (error) => {
            console.error('Error de conexión WebSocket:', error);
            
            if (this.eventHandlers['error']) {
                this.eventHandlers['error'].forEach(handler => handler(error));
            }
        });
        
        const systemEvents = [
            'system_update', 
            'system_connected', 
            'command_result'
        ];
        
        systemEvents.forEach(eventName => {
            this.socket.on(eventName, (data) => {
                console.log(`Evento recibido: ${eventName}`, data);
                
                if (this.eventHandlers[eventName]) {
                    this.eventHandlers[eventName].forEach(handler => handler(data));
                }
            });
        });
    }
    
    /**
     * Desconecta del servidor WebSocket
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            this.connected = false;
            this.clientId = null;
        }
    }
    
    /**
     * Registra un manejador para un evento
     * @param {string} event - Nombre del evento
     * @param {function} handler - Función manejadora
     */
    on(event, handler) {
        if (!this.eventHandlers[event]) {
            this.eventHandlers[event] = [];
        }
        
        this.eventHandlers[event].push(handler);
        
        if (this.socket && this.connected && !['connect', 'disconnect', 'error'].includes(event)) {
            this.socket.on(event, handler);
        }
        
        return this; //Encadenar
    }
    
    /**
     * Elimina un manejador para un evento
     * @param {string} event - Nombre del evento
     * @param {function} handler - Función manejadora (opcional)
     */
    off(event, handler) {
        if (!this.eventHandlers[event]) return this;
        
        if (handler) {
            this.eventHandlers[event] = this.eventHandlers[event]
                .filter(h => h !== handler);
        } else {
            delete this.eventHandlers[event];
        }
        
        return this;
    }
    
    /**
     * Emite un evento al servidor
     * @param {string} event - Nombre del evento
     * @param {object} data - Datos a enviar
     */
    emit(event, data) {
        if (!this.socket || !this.connected) {
            console.warn('No hay conexión WebSocket activa');
            return false;
        }
        
        this.socket.emit(event, data);
        return true;
    }
    
    /**
     * Envía un comando a un cliente específico
     * @param {string} targetId - ID del cliente destino
     * @param {string} command - Comando a ejecutar
     * @param {object} params - Parámetros del comando
     * @returns {string} ID de la solicitud
     */
    sendCommand(targetId, command, params = {}) {
        const requestId = this._generateRequestId();
        
        this.emit('execute_command', {
            target_id: targetId,
            command: command,
            params: params,
            request_id: requestId
        });
        
        return requestId;
    }
    
    /**
     * Genera un ID único para solicitudes
     * @private
     */
    _generateRequestId() {
        return 'req_' + Math.random().toString(36).substr(2, 9);
    }
}

export { WebSocketClient };