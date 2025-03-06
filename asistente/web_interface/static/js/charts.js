// Gráficos para la interfaz de usuario
let resourceChart = null;
let memoryChart = null;
let batteryChart = null;

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar gráficos
    initCharts();
});

function initCharts() {
    // Colores para gráficos
    const colors = {
        cpu: 'rgba(52, 152, 219, 0.8)',
        memory: 'rgba(155, 89, 182, 0.8)',
        battery: 'rgba(46, 204, 113, 0.8)',
        cpuBorder: 'rgba(52, 152, 219, 1)',
        memoryBorder: 'rgba(155, 89, 182, 1)',
        batteryBorder: 'rgba(46, 204, 113, 1)'
    };
    
    // Configurar gráfico de recursos
    const resourceCanvas = document.getElementById('resource-chart');
    if (resourceCanvas) {
        resourceChart = new Chart(resourceCanvas, {
            type: 'line',
            data: {
                labels: generateTimeLabels(12),
                datasets: [
                    {
                        label: 'CPU',
                        data: generateEmptyData(12),
                        backgroundColor: colors.cpu,
                        borderColor: colors.cpuBorder,
                        borderWidth: 2,
                        tension: 0.3,
                        pointRadius: 2
                    },
                    {
                        label: 'Memoria',
                        data: generateEmptyData(12),
                        backgroundColor: colors.memory,
                        borderColor: colors.memoryBorder,
                        borderWidth: 2,
                        tension: 0.3,
                        pointRadius: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Uso (%)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Tiempo'
                        }
                    }
                }
            }
        });
    }
    
    // Configurar gráfico de memoria
    const memoryCanvas = document.getElementById('memory-chart');
    if (memoryCanvas) {
        memoryChart = new Chart(memoryCanvas, {
            type: 'doughnut',
            data: {
                labels: ['Usado', 'Libre'],
                datasets: [{
                    data: [30, 70],
                    backgroundColor: [
                        colors.memory,
                        'rgba(189, 195, 199, 0.8)'
                    ],
                    borderColor: [
                        colors.memoryBorder,
                        'rgba(189, 195, 199, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                cutout: '70%'
            }
        });
    }
    
    // Configurar gráfico de batería
    const batteryCanvas = document.getElementById('battery-chart');
    if (batteryCanvas) {
        batteryChart = new Chart(batteryCanvas, {
            type: 'line',
            data: {
                labels: generateTimeLabels(24),
                datasets: [{
                    label: 'Nivel de Batería',
                    data: generateEmptyData(24),
                    backgroundColor: colors.battery,
                    borderColor: colors.batteryBorder,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3,
                    pointRadius: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Nivel (%)'
                        }
                    },
                    x: {
                        title: {
                            display: false
                        }
                    }
                }
            }
        });
    }
}

function updateResourceCharts(history) {
    if (!history) return;
    
    // Actualizar gráfico de recursos
    if (resourceChart && history.cpu && history.memory) {
        resourceChart.data.labels = history.labels || generateTimeLabels(history.cpu.length);
        resourceChart.data.datasets[0].data = history.cpu;
        resourceChart.data.datasets[1].data = history.memory;
        resourceChart.update();
    }
    
    // Actualizar gráfico de memoria
    if (memoryChart && systemData.memory) {
        const used = systemData.memory.used || 0;
        const total = systemData.memory.total || 100;
        const free = total - used;
        
        memoryChart.data.datasets[0].data = [used, free];
        memoryChart.update();
    }
    
    // Actualizar gráfico de batería
    if (batteryChart && history.battery) {
        batteryChart.data.labels = history.batteryLabels || generateTimeLabels(history.battery.length);
        batteryChart.data.datasets[0].data = history.battery;
        batteryChart.update();
    }
}

function generateTimeLabels(count) {
    const labels = [];
    const now = new Date();
    
    for (let i = count - 1; i >= 0; i--) {
        const time = new Date(now - i * 5 * 60000); // 5 minutos atrás
        labels.push(time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    }
    
    return labels;
}

function generateEmptyData(count) {
    return Array(count).fill(null);
}

// Función para actualizar gráficos con nuevos datos
function updateCharts(cpu, memory, battery) {
    // Actualizar gráfico de recursos
    if (resourceChart) {
        // Añadir nuevo punto
        resourceChart.data.datasets[0].data.push(cpu);
        resourceChart.data.datasets[1].data.push(memory);
        
        // Eliminar el punto más antiguo
        if (resourceChart.data.datasets[0].data.length > 12) {
            resourceChart.data.datasets[0].data.shift();
            resourceChart.data.datasets[1].data.shift();
            
            // Actualizar etiquetas de tiempo
            resourceChart.data.labels.shift();
            const now = new Date();
            resourceChart.data.labels.push(
                now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            );
        }
        
        resourceChart.update();
    }
    
    // Actualizar gráfico de batería
    if (batteryChart) {
        // Añadir nuevo punto
        batteryChart.data.datasets[0].data.push(battery);
        
        // Eliminar el punto más antiguo
        if (batteryChart.data.datasets[0].data.length > 24) {
            batteryChart.data.datasets[0].data.shift();
            
            // Actualizar etiquetas de tiempo
            batteryChart.data.labels.shift();
            const now = new Date();
            batteryChart.data.labels.push(
                now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            );
        }
        
        batteryChart.update();
    }
}