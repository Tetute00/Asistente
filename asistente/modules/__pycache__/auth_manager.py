#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import hashlib
import secrets
import time
from datetime import datetime, timedelta

class AuthManager:
    """Gestor de autenticación para usuarios."""
    
    def __init__(self, config_path=None):
        self.logger = logging.getLogger('AuthManager')
        self.config_path = config_path or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config/users.json')
        self.users = {}
        self.sessions = {}
        self.session_timeout = 3600  # 1 hora en segundos
        self._load_users()
        
    def _load_users(self):
        """Carga los usuarios desde el archivo de configuración."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.users = json.load(f)
                self.logger.info(f"Usuarios cargados desde {self.config_path}")
            else:
                self.users = {}
                self._save_users()  # Crear archivo vacío
                self.logger.warning(f"Archivo de usuarios no encontrado. Creando nuevo en {self.config_path}")
        except Exception as e:
            self.logger.error(f"Error al cargar usuarios: {str(e)}")
            self.users = {}
            
    def _save_users(self):
        """Guarda los usuarios al archivo de configuración."""
        try:
            # Asegurar que el directorio existe
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.users, f, indent=2)
            self.logger.info(f"Usuarios guardados en {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error al guardar usuarios: {str(e)}")
            return False
            
    def _hash_password(self, password, salt=None):
        """Crea un hash seguro para la contraseña."""
        if salt is None:
            salt = secrets.token_hex(16)
            
        # Concatenar contraseña y salt, luego aplicar hash
        hash_obj = hashlib.sha256((password + salt).encode('utf-8'))
        password_hash = hash_obj.hexdigest()
        
        return password_hash, salt
        
    def add_user(self, username, password, role='user'):
        """Añade un nuevo usuario."""
        if username in self.users:
            return False, "El usuario ya existe"
            
        # Crear hash de la contraseña
        password_hash, salt = self._hash_password(password)
        
        # Guardar información del usuario
        self.users[username] = {
            'password_hash': password_hash,
            'salt': salt,
            'role': role,
            'created': datetime.now().isoformat(),
            'last_login': None
        }
        
        # Guardar cambios
        success = self._save_users()
        return success, "Usuario creado correctamente" if success else "Error al guardar usuario"
        
    def authenticate(self, username, password):
        """Autentica un usuario."""
        if username not in self.users:
            return False, "Usuario no encontrado"
            
        user = self.users[username]
        
        # Verificar contraseña
        password_hash, _ = self._hash_password(password, user['salt'])
        if password_hash != user['password_hash']:
            return False, "Contraseña incorrecta"
            
        # Actualizar último login
        self.users[username]['last_login'] = datetime.now().isoformat()
        self._save_users()
        
        # Crear sesión
        session_token = secrets.token_urlsafe(32)
        self.sessions[session_token] = {
            'username': username,
            'role': user['role'],
            'created': datetime.now(),
            'expires': datetime.now() + timedelta(seconds=self.session_timeout)
        }
        
        return True, session_token
        
    def verify_session(self, session_token):
        """Verifica si una sesión es válida."""
        if session_token not in self.sessions:
            return False, "Sesión inválida"
            
        session = self.sessions[session_token]
        
        # Verificar si la sesión ha expirado
        if datetime.now() > session['expires']:
            del self.sessions[session_token]
            return False, "Sesión expirada"
            
        # Extender tiempo de sesión
        session['expires'] = datetime.now() + timedelta(seconds=self.session_timeout)
        
        return True, session
        
    def logout(self, session_token):
        """Cierra una sesión."""
        if session_token in self.sessions:
            del self.sessions[session_token]
            return True
        return False
        
    def change_password(self, username, old_password, new_password):
        """Cambia la contraseña de un usuario."""
        if username not in self.users:
            return False, "Usuario no encontrado"
            
        # Verificar contraseña antigua
        valid, _ = self.authenticate(username, old_password)
        if not valid:
            return False, "Contraseña actual incorrecta"
            
        # Crear hash de la nueva contraseña
        password_hash, salt = self._hash_password(new_password)
        
        # Actualizar información
        self.users[username]['password_hash'] = password_hash
        self.users[username]['salt'] = salt
        
        # Guardar cambios
        success = self._save_users()
        return success, "Contraseña actualizada correctamente" if success else "Error al guardar"