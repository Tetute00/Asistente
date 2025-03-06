// Main application JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Inicialización
    initApp();
    
    // Gestión de navegación
    setupNavigation();
    
    // Configurar eventos de UI
    setupUIEvents();
    
    // Gestionar autenticación
    setupAuth();
});

// Variables globales
let refreshInterval = null;
let currentPage = 'dashboard';
const refreshTime = 10000; // 10 segundos por defecto
const systemData = {};
let isLoggedIn = false;

// Inicialización de la aplicación
function initApp() {
    console.log('Inicializando aplicación...');
    
    // Comprobar tema guardado
    const savedTheme = localStorage.getItem('theme') || 'auto';
    setTheme(savedTheme);
    
    // Actualizar fecha/hora actual
    updateDateTime();
    setInterval(updateDateTime, 1000);
    
    // Mostrar login si no hay sesión
    checkSession();
}

// Configurar navegación
function setupNavigation() {
    const navLinks = document.querySelectorAll('.navbar-menu a');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            
            // Actualizar enlaces activos
            navLinks.forEach(navLink => navLink.classList.remove('active'));
            this.classList.add('active');
            
            // Mostrar página correspondiente
            const pages = document.querySelectorAll('.page');
            pages.forEach(page => {
                if (page.id === targetId) {
                    page.classList.add('active');
                    currentPage = targetId;
                    
                    // Inicializar contenido de la página cuando se cambia a ella
                    initPageContent(targetId);
                } else {
                    page.classList.remove('active');
                }
            });
        });
    });
}

// Inicializar contenido específico de cada página
function initPageContent(pageId) {
    switch (pageId) {
        case 'dashboard':
            fetchSystemData();
            refreshInterval = setInterval(fetchSystemData, refreshTime);
            break;
        case 'system':
            fetchDetailedSystemInfo();
            break;
        case 'remote':
            fetchDeviceList();
            break;
        case 'voice':
            // Código específico para la página de voz
            break;
        case 'settings':
            loadSettings();
            break;
        default:
            break;
    }
}

// Configurar eventos de UI
function setupUIEvents() {
    // Botones de acción rápida
    document.getElementById('btn-mute').addEventListener('click', toggleMute);
    document.getElementById('btn-command').addEventListener('click', showCommandPrompt);
    document.getElementById('btn-refresh').addEventListener('click', refreshCurrentPage);
    document.getElementById('btn-help').addEventListener('click', showHelp);
    
    // Modal de añadir dispositivo
    document.getElementById('btn-add-device').addEventListener('click', showAddDeviceModal);
    document.getElementById('btn-cancel-add-device').addEventListener('click', hideAddDeviceModal);
    document.getElementById('btn-confirm-add-device').addEventListener('click', addNewDevice);
    
    // Cerrar modal con X
    document.querySelectorAll('.close-modal').forEach(closeBtn => {
        closeBtn.addEventListener('click', function() {
            document.querySelectorAll('.modal').forEach(modal => {
                modal.style.display = 'none';
            });
        });
    });
    
    // Eventos de voz
    document.getElementById('btn-start-listening').addEventListener('click', startVoiceListening);
    document.getElementById('btn-stop-listening').addEventListener('click', stopVoiceListening);
    document.getElementById('btn-send-message').addEventListener('click', sendChatMessage);
    document.getElementById('message-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });
    
    // Eventos de configuración
    document.getElementById('voice-rate').addEventListener('input', updateVoiceRateValue);
    document.getElementById('voice-volume').addEventListener('input', updateVoiceVolumeValue);
    document.getElementById('btn-test-voice').addEventListener('click', testVoice);
    
    // Consola remota
    document.getElementById('command-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            executeCommand();
        }
    });
    
    // Botones de comando rápido
    document.querySelectorAll('.cmd-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const cmd = this.getAttribute('data-cmd');
            document.getElementById('command-input').value = cmd;
            executeCommand();
        });
    });
}

// Gestión de autenticación
function setupAuth() {
    document.getElementById('login-button').addEventListener('click', login);
    document.getElementById('logout-button').addEventListener('click', logout);
}

function login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    if (!username || !password) {
        showLoginError('Por favor, ingrese usuario y contraseña');
        return;
    }
    
    // Simular autenticación (reemplazar con llamada real a API)
    fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            localStorage.setItem('session_token', data.token);
            isLoggedIn = true;
            hideLoginOverlay();
            document.getElementById('username-display').textContent = username;
            
            // Actualizar interfaz con datos del sistema
            fetchSystemData();
        } else {
            showLoginError(data.message || 'Error de autenticación');
        }
    })
    .catch(error => {
        console.error('Error de login:', error);
        showLoginError('Error al conectar con el servidor');
    });
}

function logout() {
    // Limpiar datos de sesión
    localStorage.removeItem('session_token');
    isLoggedIn = false;
    
    // Detener actualizaciones automáticas
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    // Mostrar pantalla de login
    showLoginOverlay();
}

function checkSession() {
    const token = localStorage.getItem('session_token');
    
    if (!token) {
        showLoginOverlay();
        return;
    }
    
    // Verificar token con el servidor
    fetch('/api/auth/verify', {
        headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(response => response.json())
    .then(data => {
        if (data.valid) {
            isLoggedIn = true;
            hideLoginOverlay();
            document.getElementById('username-display').textContent = data.username;
            
            // Inicializar datos
            fetchSystemData();
        } else {
            showLoginOverlay();
        }
    })
    .catch(() => {
        // En caso de error, mostrar login
        showLoginOverlay();
    });
}

function showLoginOverlay() {
    document.getElementById('login-overlay').style.display = 'flex';
}

function hideLoginOverlay() {
    document.getElementById('login-overlay').style.display = 'none';
}

function showLoginError(message) {
    document.getElementById('login-error').textContent = message;
}

// Funciones para gestionar datos del sistema
function fetchSystemData() {
    if (!isLoggedIn) return;
    
    fetch('/api/system/status')
        .then(response => response.json())
        .then(data => {
            systemData.cpu = data.cpu || {};
            systemData.memory = data.memory || {};
            systemData.battery = data.battery || {};
            systemData.system_info = data.system_info || {};
            
            // Actualizar UI
            updateSystemUI();
        })
        .catch(error => {
            console.error('Error al obtener datos del sistema:', error);
        });
}

function updateSystemUI() {
    // Actualizar indicadores de CPU
    const cpuProgress = document.getElementById('cpu-progress');
    if (cpuProgress) {
        const cpuPercent = systemData.cpu.percent || 0;
        cpuProgress.style.width = `${cpuPercent}%`;
        cpuProgress.textContent = `${cpuPercent}%`;
        
        // Cambiar color según uso
        if (cpuPercent > 80) {
            cpuProgress.style.backgroundColor = 'var(--danger-color)';
        } else if (cpuPercent > 60) {
            cpuProgress.style.backgroundColor = 'var(--warning-color)';
        } else {
            cpuProgress.style.backgroundColor = 'var(--primary-color)';
        }
    }
    
    // Actualizar indicadores de memoria
    const memoryProgress = document.getElementById('memory-progress');
    if (memoryProgress && systemData.memory) {
        const memoryPercent = systemData.memory.percent || 0;
        memoryProgress.style.width = `${memoryPercent}%`;
        memoryProgress.textContent = `${memoryPercent}%`;
        
        // Cambiar color según uso
        if (memoryPercent > 80) {
            memoryProgress.style.backgroundColor = 'var(--danger-color)';
        } else if (memoryPercent > 60) {
            memoryProgress.style.backgroundColor = 'var(--warning-color)';
        } else {
            memoryProgress.style.backgroundColor = 'var(--primary-color)';
        }
        
        // Actualizar detalles de memoria en la página Sistema
        if (currentPage === 'system' && systemData.memory) {
            document.getElementById('memory-total').textContent = `${(systemData.memory.total / 1024).toFixed(1)} GB`;
            document.getElementById('memory-used').textContent = `${(systemData.memory.used / 1024).toFixed(1)} GB`;
            document.getElementById('memory-free').textContent = 
                `${((systemData.memory.total - systemData.memory.used) / 1024).toFixed(1)} GB`;
        }
    }
    
    // Actualizar información de batería
    if (systemData.battery) {
        const batteryProgress = document.getElementById('battery-progress');
        const batteryStatus = document.getElementById('battery-status');
        const batteryLevel = document.getElementById('battery-level');
        const batteryIcon = document.getElementById('battery-icon');
        const batteryPercent = document.getElementById('battery-percent');
        const chargingStatus = document.getElementById('charging-status');
        const timeRemaining = document.getElementById('time-remaining');
        
        const batteryPercentValue = systemData.battery.percent || 0;
        
        if (batteryProgress) {
            batteryProgress.style.width = `${batteryPercentValue}%`;
            batteryProgress.textContent = `${batteryPercentValue}%`;
            
            // Cambiar color según nivel
            if (batteryPercentValue < 20) {
                batteryProgress.style.backgroundColor = 'var(--danger-color)';
            } else if (batteryPercentValue < 50) {
                batteryProgress.style.backgroundColor = 'var(--warning-color)';
            } else {
                batteryProgress.style.backgroundColor = 'var(--success-color)';
            }
        }
        
        if (batteryStatus) {
            const isCharging = systemData.battery.charging;
            const timeLeft = systemData.battery.time_left;
            batteryStatus.textContent = isCharging ? 
                `Cargando - ${timeLeft}` : `Descargando - ${timeLeft}`;
        }
        
        if (batteryLevel) batteryLevel.textContent = `${batteryPercentValue}%`;
        if (batteryPercent) batteryPercent.textContent = `${batteryPercentValue}%`;
        
        if (chargingStatus && systemData.battery.charging !== undefined) {
            chargingStatus.textContent = systemData.battery.charging ? 'Cargando' : 'Descargando';
        }
        
        if (timeRemaining) {
            timeRemaining.textContent = systemData.battery.time_left;
        }
        
        // Actualizar el ícono de batería
        if (batteryIcon) {
            let iconClass = 'fa-battery-empty';
            if (batteryPercentValue > 87) iconClass = 'fa-battery-full';
            else if (batteryPercentValue > 62) iconClass = 'fa-battery-three-quarters';
            else if (batteryPercentValue > 37) iconClass = 'fa-battery-half';
            else if (batteryPercentValue > 12) iconClass = 'fa-battery-quarter';
            
            batteryIcon.className = `fas ${iconClass}`;
            
            // Añadir ícono de carga si corresponde
            if (systemData.battery.charging) {
                batteryIcon.className += ' charging';
            }
        }
    }
    
    // Actualizar información del sistema
    if (systemData.system_info) {
        const systemInfoElement = document.getElementById('system-info');
        if (systemInfoElement) {
            systemInfoElement.textContent = `${systemData.system_info.os} - ${systemData.system_info.os_version}`;
        }
        
        // Actualizar detalles del sistema en la página Sistema
        if (currentPage === 'system') {
            document.getElementById('os-info').textContent = systemData.system_info.os || 'Desconocido';
            document.getElementById('os-version').textContent = systemData.system_info.os_version || 'Desconocido';
            document.getElementById('hostname').textContent = systemData.system_info.hostname || 'Desconocido';
            document.getElementById('processor').textContent = systemData.system_info.processor || 'Desconocido';
        }
    }
}

// Funciones para actualizar fecha y hora
function updateDateTime() {
    const now = new Date();
    document.getElementById('current-time').textContent = now.toLocaleString();
}

// Funciones para acciones rápidas
function toggleMute() {
    // Implementar lógica para silencio
    fetch('/api/system/mute', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.muted) {
                document.getElementById('btn-mute').querySelector('i').className = 'fas fa-volume-mute';
            } else {
                document.getElementById('btn-mute').querySelector('i').className = 'fas fa-volume-up';
            }
        })
        .catch(error => {
            console.error('Error al cambiar estado de silencio:', error);
        });
}

function showCommandPrompt() {
    // Hacer foco en el campo de comandos
    document.querySelector('.navbar-menu a[href="#remote"]').click();
    setTimeout(() => {
        document.getElementById('command-input').focus();
    }, 300);
}

function refreshCurrentPage() {
    // Actualizar datos de la página actual
    switch (currentPage) {
        case 'dashboard':
            fetchSystemData();
            break;
        case 'system':
            fetchDetailedSystemInfo();
            break;
        case 'remote':
            fetchDeviceList();
            break;
        case 'voice':
            // Refrescar datos de voz
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

function showHelp() {
    // Mostrar modal de ayuda o redireccionar a página de ayuda
    document.querySelector('.navbar-menu a[href="#voice"]').click();
    setTimeout(() => {
        document.getElementById('commands-list').scrollIntoView({
            behavior: 'smooth'
        });
    }, 300);
}

// Funciones para gestión de dispositivos remotos
function showAddDeviceModal() {
    document.getElementById('add-device-modal').style.display = 'flex';
}

function hideAddDeviceModal() {
    document.getElementById('add-device-modal').style.display = 'none';
    document.getElementById('add-device-form').reset();
}

function addNewDevice() {
    const form = document.getElementById('add-device-form');
    
    const name = document.getElementById('device-name').value;
    const ip = document.getElementById('device-ip').value;
    const port = document.getElementById('device-port').value;
    const type = document.getElementById('device-type').value;
    const token = document.getElementById('device-token').value;
    
    if (!name || !ip || !port) {
        alert('Por favor, complete todos los campos obligatorios');
        return;
    }
    
    // Enviar datos al servidor
    fetch('/api/remote/device', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, ip, port, type, token })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            hideAddDeviceModal();
            fetchDeviceList();
            
            // Añadir al log de actividad
            addActivityLog(`Dispositivo ${name} añadido`);
        } else {
            alert(data.message || 'Error al añadir dispositivo');
        }
    })
    .catch(error => {
        console.error('Error al añadir dispositivo:', error);
        alert('Error de conexión al intentar añadir el dispositivo');
    });
}

function fetchDeviceList() {
    fetch('/api/remote/devices')
        .then(response => response.json())
        .then(data => {
            updateDeviceList(data.devices || []);
            updateDeviceSelector(data.devices || []);
        })
        .catch(error => {
            console.error('Error al obtener lista de dispositivos:', error);
        });
}

function updateDeviceList(devices) {
    const tableBody = document.getElementById('devices-table-body');
    if (!tableBody) return;
    
    tableBody.innerHTML = '';
    
    devices.forEach(device => {
        const row = document.createElement('tr');
        
        const statusClass = device.online ? 'online' : 'offline';
        const statusText = device.online ? 'Online' : 'Offline';
        
        row.innerHTML = `
            <td>${device.name}</td>
            <td><span class="status ${statusClass}">${statusText}</span></td>
            <td>${device.ip}</td>
            <td>
                <button class="btn small info" onclick="openConsole('${device.name}')" ${!device.online ? 'disabled' : ''}>
                    <i class="fas fa-terminal"></i>
                </button>
                <button class="btn small danger" onclick="removeDevice('${device.name}')">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    if (devices.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center;">No hay dispositivos configurados</td>
            </tr>
        `;
    }
}

function updateDeviceSelector(devices) {
    const selector = document.getElementById('device-selector');
    if (!selector) return;
    
    // Preservar opción local
    const currentValue = selector.value;
    selector.innerHTML = '<option value="local">Este dispositivo</option>';
    
    devices.forEach(device => {
        if (device.online) {
            const option = document.createElement('option');
            option.value = device.name;
            option.textContent = device.name;
            selector.appendChild(option);
        }
    });
    
    // Intentar restaurar la selección anterior
    if (devices.some(d => d.name === currentValue)) {
        selector.value = currentValue;
    }
}

function openConsole(deviceName) {
    document.getElementById('device-selector').value = deviceName;
    addConsoleOutput(`Conectado a ${deviceName}`);
    document.getElementById('command-input').focus();
}

function removeDevice(deviceName) {
    if (!confirm(`¿Estás seguro de que deseas eliminar el dispositivo "${deviceName}"?`)) {
        return;
    }
    
    fetch(`/api/remote/device/${encodeURIComponent(deviceName)}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            fetchDeviceList();
            addActivityLog(`Dispositivo ${deviceName} eliminado`);
        } else {
            alert(data.message || 'Error al eliminar dispositivo');
        }
    })
    .catch(error => {
        console.error('Error al eliminar dispositivo:', error);
        alert('Error de conexión al intentar eliminar el dispositivo');
    });
}

// Funciones para la consola remota
function executeCommand() {
    const commandInput = document.getElementById('command-input');
    const command = commandInput.value.trim();
    const deviceSelector = document.getElementById('device-selector');
    const device = deviceSelector.value;
    
    if (!command) return;
    
    // Mostrar comando en consola
    addConsoleOutput(`$ ${command}`, 'command');
    
    // Limpiar input
    commandInput.value = '';
    
    // Ejecutar comando
    if (device === 'local') {
        // Comando en dispositivo local
        executeLocalCommand(command);
    } else {
        // Comando en dispositivo remoto
        executeRemoteCommand(device, command);
    }
}

function executeLocalCommand(command) {
    fetch('/api/system/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addConsoleOutput(data.output || 'Comando ejecutado correctamente');
        } else {
            addConsoleOutput(`Error: ${data.error || 'Error desconocido'}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error al ejecutar comando local:', error);
        addConsoleOutput('Error de conexión', 'error');
    });
}

function executeRemoteCommand(device, command) {
    fetch('/api/remote/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ device, command })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addConsoleOutput(data.output || 'Comando ejecutado correctamente');
        } else {
            addConsoleOutput(`Error: ${data.error || 'Error desconocido'}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error al ejecutar comando remoto:', error);
        addConsoleOutput('Error de conexión', 'error');
    });
}

function addConsoleOutput(text, type = 'output') {
    const consoleOutput = document.getElementById('console-output');
    
    const line = document.createElement('div');
    line.className = `output-line ${type}`;
    line.textContent = text;
    
    consoleOutput.appendChild(line);
    
    // Scroll al final
    consoleOutput.scrollTop = consoleOutput.scrollHeight;
}

// Funciones para el asistente de voz
let isListening = false;

function startVoiceListening() {
    if (isListening) return;
    
    isListening = true;
    
    // Cambiar estado de botones
    document.getElementById('btn-start-listening').disabled = true;
    document.getElementById('btn-stop-listening').disabled = false;
    
    // Cambiar estado visual
    document.getElementById('voice-status').textContent = 'Escuchando...';
    document.getElementById('voice-waves').classList.add('active');
    
    // Iniciar reconocimiento de voz
    fetch('/api/voice/listen', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // La respuesta llegará por WebSocket o por polling
                pollVoiceResults();
            } else {
                stopVoiceListening();
                alert(data.message || 'Error al iniciar reconocimiento de voz');
            }
        })
        .catch(error => {
            console.error('Error al iniciar reconocimiento de voz:', error);
            stopVoiceListening();
        });
}

function stopVoiceListening() {
    if (!isListening) return;
    
    isListening = false;
    
    // Cambiar estado de botones
    document.getElementById('btn-start-listening').disabled = false;
    document.getElementById('btn-stop-listening').disabled = true;
    
    // Cambiar estado visual
    document.getElementById('voice-status').textContent = 'Esperando...';
    document.getElementById('voice-waves').classList.remove('active');
    
    // Detener reconocimiento de voz
    fetch('/api/voice/stop', { method: 'POST' })
        .catch(error => {
            console.error('Error al detener reconocimiento de voz:', error);
        });
}

function pollVoiceResults() {
    if (!isListening) return;
    
    fetch('/api/voice/results')
        .then(response => response.json())
        .then(data => {
            if (data.text) {
                // Se ha reconocido texto
                addChatMessage(data.text, 'user');
                
                // Procesar con IA
                if (data.response) {
                    addChatMessage(data.response, 'system');
                }
                
                // Si el reconocimiento sigue activo, seguir sondeando
                if (isListening) {
                    setTimeout(pollVoiceResults, 1000);
                }
            } else {
                // No hay resultados, seguir sondeando
                setTimeout(pollVoiceResults, 1000);
            }
            
            // Si se ha detenido el reconocimiento
            if (data.listening === false) {
                stopVoiceListening();
            }
        })
        .catch(error => {
            console.error('Error al obtener resultados de voz:', error);
            setTimeout(pollVoiceResults, 2000); // Reintentar con un intervalo mayor
        });
}

function sendChatMessage() {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Limpiar input
    messageInput.value = '';
    
    // Añadir mensaje al chat
    addChatMessage(message, 'user');
    
    // Procesar con IA
    fetch('/api/voice/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: message })
    })
    .then(response => response.json())
    .then(data => {
        if (data.response) {
            addChatMessage(data.response, 'system');
        }
    })
    .catch(error => {
        console.error('Error al procesar mensaje:', error);
        addChatMessage('Error al procesar mensaje', 'system');
    });
}

function addChatMessage(text, role) {
    const chatContainer = document.getElementById('chat-container');
    const now = new Date();
    const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;
    
    messageDiv.innerHTML = `
        <div class="message-content">${text}</div>
        <div class="message-time">${timeString}</div>
    `;
    
    chatContainer.appendChild(messageDiv);
    
    // Scroll al final
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // Añadir al log de actividad si viene del sistema
    if (role === 'system') {
        addActivityLog(`Asistente: ${text.substring(0, 30)}${text.length > 30 ? '...' : ''}`);
    }
}

// Funciones para configuración de voz
function updateVoiceRateValue() {
    const rateSlider = document.getElementById('voice-rate');
    const rateValue = document.getElementById('voice-rate-value');
    
    if (rateSlider && rateValue) {
        rateValue.textContent = rateSlider.value;
    }
}

function updateVoiceVolumeValue() {
    const volumeSlider = document.getElementById('voice-volume');
    const volumeValue = document.getElementById('voice-volume-value');
    
    if (volumeSlider && volumeValue) {
        volumeValue.textContent = volumeSlider.value;
    }
}

function testVoice() {
    const rate = document.getElementById('voice-rate').value;
    const volume = document.getElementById('voice-volume').value;
    
    fetch('/api/voice/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rate, volume, text: 'Prueba de voz del asistente' })
    })
    .catch(error => {
        console.error('Error al probar voz:', error);
    });
}

// Funciones para información detallada del sistema
function fetchDetailedSystemInfo() {
    // Ya tenemos la información básica, pero podemos solicitar datos adicionales
    fetch('/api/system/detailed')
        .then(response => response.json())
        .then(data => {
            // Actualizar información de tiempo de actividad
            if (data.uptime) {
                document.getElementById('uptime').textContent = data.uptime;
            }
            
            // Actualizar información de batería
            if (data.battery && data.battery.cycles) {
                document.getElementById('battery-cycles').textContent = data.battery.cycles;
            }
            
            // Actualizar gráficos con el historial
            if (data.history) {
                updateResourceCharts(data.history);
            }
        })
        .catch(error => {
            console.error('Error al obtener información detallada:', error);
        });
}

// Funciones para gestión de preferencias
function loadSettings() {
    fetch('/api/settings')
        .then(response => response.json())
        .then(data => {
            // Configurar sliders
            if (data.voice) {
                document.getElementById('voice-rate').value = data.voice.rate || 150;
                document.getElementById('voice-volume').value = data.voice.volume || 0.8;
                document.getElementById('wake-word').value = data.voice.wake_word || 'casa';
                
                // Actualizar valores mostrados
                updateVoiceRateValue();
                updateVoiceVolumeValue();
            }
            
            // Configurar opciones del sistema
            if (data.system) {
                document.getElementById('refresh-interval').value = data.system.refresh_interval || 10;
                document.getElementById('theme-selector').value = data.system.theme || 'auto';
                document.getElementById('auto-start').checked = data.system.auto_start !== false;
                document.getElementById('log-activity').checked = data.system.log_activity !== false;
                document.getElementById('notifications').checked = data.system.notifications !== false;
            }
        })
        .catch(error => {
            console.error('Error al cargar configuración:', error);
        });
}

// Funciones para el registro de actividad
function addActivityLog(message) {
    const activityList = document.getElementById('activity-list');
    if (!activityList) return;
    
    const now = new Date();
    const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    const listItem = document.createElement('li');
    listItem.innerHTML = `<span class="time">${timeString}</span> <span class="event">${message}</span>`;
    
    // Insertar al principio
    activityList.insertBefore(listItem, activityList.firstChild);
    
    // Limitar a 10 elementos
    while (activityList.children.length > 10) {
        activityList.removeChild(activityList.lastChild);
    }
}

// Funciones para gestión de tema
function setTheme(theme) {
    const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Guardar preferencia
    localStorage.setItem('theme', theme);
    
    if (theme === 'auto') {
        document.body.classList.toggle('dark-theme', prefersDarkMode);
    } else if (theme === 'dark') {
        document.body.classList.add('dark-theme');
    } else {
        document.body.classList.remove('dark-theme');
    }
    
    // Actualizar selector si existe
    const themeSelector = document.getElementById('theme-selector');
    if (themeSelector) {
        themeSelector.value = theme;
    }
}

// Escuchar cambios en el esquema de colores del sistema
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    const theme = localStorage.getItem('theme') || 'auto';
    if (theme === 'auto') {
        document.body.classList.toggle('dark-theme', e.matches);
    }
});

// Inicializar pantalla de bloqueo al inicio
document.getElementById('login-overlay').style.display = 'flex';