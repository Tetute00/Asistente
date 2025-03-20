#!/usr/bin/env python
"""
JARVIS - Just A Rather Very Intelligent System
Servidor principal "Chromebook"
"""

from flask import Flask, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
import os
import logging
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("jarvis.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("JARVIS")

load_dotenv()

# Iniciar server
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

from websockets.manager import WebSocketManager

# Iniciar WebSockets
ws_manager = WebSocketManager(socketio)

@app.route('/')
def index():
    return jsonify({
        "name": "JARVIS API",
        "status": "online",
        "version": "0.1.0"
    })

@app.route('/api/system/status')
def system_status():
    # Respuesta "falsa"
    return jsonify({
        "is_online": True,
        "current_os": "unknown",
        "cpu_usage": 0,
        "ram_usage": 0,
        "uptime": 0,
        "last_update": "2025-03-19T18:20:33Z"
    })

@app.route('/api/clients')
def client_list():
    """Devuelve la lista de clientes conectados"""
    clients = []
    for client_id, client_data in ws_manager.clients.items():
        clients.append({
            'id': client_id,
            'type': client_data.get('type', 'unknown'),
            'name': client_data.get('name', f"Client {client_id[:8]}"),
            'connected_at': client_data.get('connected_at')
        })
    
    return jsonify({
        "count": len(clients),
        "clients": clients
    })

if __name__ == '__main__':
    port = int(os.environ.get('SERVER_PORT', 5000))
    logger.info(f"Iniciando servidor JARVIS en puerto {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=True)