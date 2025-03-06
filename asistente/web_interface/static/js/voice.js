// Funcionalidad de visualización de voz
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar visualización de ondas de voz
    initVoiceVisualizer();
});

function initVoiceVisualizer() {
    const wavesContainer = document.getElementById('voice-waves');
    if (!wavesContainer) return;
    
    // Crear ondas
    for (let i = 0; i < 5; i++) {
        const wave = document.createElement('div');
        wave.className = 'wave';
        wavesContainer.appendChild(wave);
    }
    
    // Botón para limpiar conversación
    document.getElementById('btn-clear-conversation').addEventListener('click', clearConversation);
}

function clearConversation() {
    const chatContainer = document.getElementById('chat-container');
    
    // Mantener solo el mensaje de bienvenida
    chatContainer.innerHTML = `
        <div class="chat-message system">
            <div class="message-content">
                Hola, soy tu asistente. ¿En qué puedo ayudarte?
            </div>
            <div class="message-time">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
        </div>
    `;
}

// Animación de ondas de voz cuando está escuchando
function animateVoiceWaves(isActive) {
    const waves = document.querySelectorAll('#voice-waves .wave');
    
    if (isActive) {
        waves.forEach((wave, index) => {
            wave.style.animation = `wave ${1 + index * 0.2}s ease-in-out infinite alternate`;
            wave.style.height = `${20 + index * 10}px`;
            wave.style.opacity = '1';
        });
    } else {
        waves.forEach(wave => {
            wave.style.animation = 'none';
            wave.style.height = '5px';
            wave.style.opacity = '0.3';
        });
    }
}

// Activa/desactiva la animación cuando cambia el estado de escucha
document.addEventListener('DOMContentLoaded', function() {
    const startButton = document.getElementById('btn-start-listening');
    const stopButton = document.getElementById('btn-stop-listening');
    
    if (startButton) {
        startButton.addEventListener('click', function() {
            animateVoiceWaves(true);
        });
    }
    
    if (stopButton) {
        stopButton.addEventListener('click', function() {
            animateVoiceWaves(false);
        });
    }
});