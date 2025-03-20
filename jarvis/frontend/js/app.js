/**
 * Aplicación principal de JARVIS
 * Coordina los diferentes componentes
 */

import { WebSocketClient } from './websocket.js';
import { SystemMonitor } from './components/system-monitor.js';

class JarvisApp {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000/api';
        this.wsClient = new WebSocketClient('http://localhost:5000');
        
        // Inicializar componentes
        this.systemMonitor = new SystemMonitor(
            document.querySelector('.system-status')
        );
        
        // Inicializar la aplicación
        this.initialize();
    }
    
    /**
     * Inicializa la aplicación
     */
    initialize() {
        console.log('Iniciando JARVIS Web Interface...');
        
        // Conectar WebSockets
        this.wsClient.connect();
        
        // Configurar handlers de WebSocket
        this.wsClient.on('connect', () => {
            console.log('Conectado al servidor JARVIS');
            this.updateStatus('online');
        });
        
        this.wsClient.on('disconnect', () => {
            console.log('Desconectado del servidor JARVIS');
            this.updateStatus('offline');
        });
        
        this.wsClient.on('system_update', (data) => {
            console.log('Actualización del sistema recibida:', data);
            this.systemMonitor.updateData(data);
        });
        
        // Cargar datos iniciales
        this.loadInitialData();
        
        // Configurar actualización automática
        this.systemMonitor.startAutoRefresh(10000); // Cada 10 segundos
    }
    
    /**
     * Carga los datos iniciales desde el servidor
     */
    loadInitialData() {
        fetch(`${this.apiBaseUrl}/system/status`)
            .then(response => response.json())
            .then(data => {
                this.systemMonitor.updateData(data);
            })
            .catch(error => {
                console.error('Error cargando datos iniciales:', error);
            });
    }
    
    /**
     * Actualiza el indicador de estado general
     * @param {string} status - Estado ('online' u 'offline')
     */
    updateStatus(status) {
        const statusIndicator = document.querySelector('header .status-indicator');
        const statusText = document.querySelector('header .status-indicator .text');
        
        if (status === 'online') {
            statusIndicator.className = 'status-indicator online';
            statusText.textContent = 'Online';
        } else {
            statusIndicator.className = 'status-indicator offline';
            statusText.textContent = 'Offline';
        }
    }
}

// Iniciar aplicacion
document.addEventListener('DOMContentLoaded', () => {
    window.jarvisApp = new JarvisApp();
});