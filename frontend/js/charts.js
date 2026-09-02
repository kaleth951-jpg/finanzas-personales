/**
 * Fiskal - Módulo de Visualizaciones Gráficas con Chart.js
 */

const ChartsManager = {
    doughnutInstance: null,
    trendInstance: null,

    /**
     * Paleta de colores de respaldo para categorías sin color asignado
     */
    fallbackColors: [
        '#6366f1', '#10b981', '#f59e0b', '#ec4899', 
        '#3b82f6', '#8b5cf6', '#ef4444', '#06b6d4', 
        '#84cc16', '#a855f7', '#f97316', '#14b8a6'
    ],

    /**
     * Formateador de moneda en formato USD/Moneda
     */
    formatCurrency(value) {
        return new Intl.NumberFormat('es-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2
        }).format(value);
    },

    /**
     * Configura opciones globales predeterminadas de Chart.js
     */
    initGlobalDefaults() {
        if (typeof Chart === 'undefined') return;

        Chart.defaults.color = '#94a3b8';
        Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
        Chart.defaults.font.size = 12;
        Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15, 23, 42, 0.95)';
        Chart.defaults.plugins.tooltip.titleColor = '#f8fafc';
        Chart.defaults.plugins.tooltip.bodyColor = '#cbd5e1';
        Chart.defaults.plugins.tooltip.borderColor = 'rgba(255, 255, 255, 0.12)';
        Chart.defaults.plugins.tooltip.borderWidth = 1;
        Chart.defaults.plugins.tooltip.padding = 10;
        Chart.defaults.plugins.tooltip.cornerRadius = 8;
    },

    /**
     * Renderiza el gráfico de dona de distribución de gastos por categoría
     */
    renderCategoryDoughnut(canvasId, items = []) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        if (this.doughnutInstance) {
            this.doughnutInstance.destroy();
            this.doughnutInstance = null;
        }

        const centerAmountEl = document.getElementById('doughnutTotalAmount');

        if (!items || items.length === 0) {
            if (centerAmountEl) centerAmountEl.textContent = '$0.00';
            const ctx = canvas.getContext('2d');
            this.doughnutInstance = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Sin Gastos'],
                    datasets: [{
                        data: [1],
                        backgroundColor: ['rgba(255, 255, 255, 0.08)'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '72%',
                    plugins: {
                        legend: { display: false },
                        tooltip: { enabled: false }
                    }
                }
            });
            return;
        }

        const labels = items.map(i => i.categoria);
        const data = items.map(i => i.total);
        const totalSum = data.reduce((acc, curr) => acc + curr, 0);
        const colors = items.map((i, idx) => i.color || this.fallbackColors[idx % this.fallbackColors.length]);

        if (centerAmountEl) {
            centerAmountEl.textContent = this.formatCurrency(totalSum);
        }

        const ctx = canvas.getContext('2d');
        this.doughnutInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderColor: '#111726',
                    borderWidth: 3,
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#cbd5e1',
                            padding: 14,
                            usePointStyle: true,
                            pointStyle: 'circle',
                            font: { size: 11, weight: '500' }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const val = context.raw || 0;
                                const pct = totalSum > 0 ? ((val / totalSum) * 100).toFixed(1) : 0;
                                return ` ${context.label}: ${this.formatCurrency(val)} (${pct}%)`;
                            }
                        }
                    }
                },
                animation: {
                    animateScale: true,
                    animateRotate: true,
                    duration: 800
                }
            }
        });
    },

    /**
     * Renderiza el gráfico de líneas y barras comparativo histórico de Ingresos vs. Gastos
     */
    renderMonthlyTrendChart(canvasId, items = []) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        if (this.trendInstance) {
            this.trendInstance.destroy();
            this.trendInstance = null;
        }

        const ctx = canvas.getContext('2d');

        if (!items || items.length === 0) {
            this.trendInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: ['Sin Datos'],
                    datasets: []
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } }
                }
            });
            return;
        }

        const labels = items.map(i => i.periodo);
        const dataIngresos = items.map(i => i.ingresos);
        const dataGastos = items.map(i => i.gastos);
        const dataBalance = items.map(i => i.balance);

        // Gradientes para ingresos y gastos
        const gradIncome = ctx.createLinearGradient(0, 0, 0, 300);
        gradIncome.addColorStop(0, 'rgba(16, 185, 129, 0.35)');
        gradIncome.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

        const gradExpense = ctx.createLinearGradient(0, 0, 0, 300);
        gradExpense.addColorStop(0, 'rgba(244, 63, 94, 0.35)');
        gradExpense.addColorStop(1, 'rgba(244, 63, 94, 0.0)');

        this.trendInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Ingresos',
                        data: dataIngresos,
                        borderColor: '#10b981',
                        backgroundColor: gradIncome,
                        borderWidth: 2.5,
                        fill: true,
                        tension: 0.35,
                        pointBackgroundColor: '#10b981',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 1.5,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    },
                    {
                        label: 'Gastos',
                        data: dataGastos,
                        borderColor: '#f43f5e',
                        backgroundColor: gradExpense,
                        borderWidth: 2.5,
                        fill: true,
                        tension: 0.35,
                        pointBackgroundColor: '#f43f5e',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 1.5,
                        pointRadius: 4,
                        pointHoverRadius: 6
                    },
                    {
                        label: 'Balance Neto',
                        data: dataBalance,
                        borderColor: '#6366f1',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0.2,
                        pointBackgroundColor: '#6366f1',
                        pointRadius: 3,
                        pointHoverRadius: 5
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            font: { size: 11 }
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#94a3b8',
                            callback: (value) => `$${value >= 1000 ? (value / 1000).toFixed(1) + 'k' : value}`
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        align: 'end',
                        labels: {
                            color: '#cbd5e1',
                            usePointStyle: true,
                            padding: 12,
                            font: { size: 11, weight: '600' }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                return ` ${context.dataset.label}: ${this.formatCurrency(context.raw)}`;
                            }
                        }
                    }
                },
                animation: {
                    duration: 900
                }
            }
        });
    }
};

// Inicializar configuraciones globales al cargar
ChartsManager.initGlobalDefaults();
