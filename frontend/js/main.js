/**
 * Fiskal - Controlador Principal del Frontend
 * Gestión Inteligente de Finanzas Personales & Motor de Analítica
 */

// Estado global de la aplicación
const AppState = {
    activeUserId: null,
    activeMonth: '',
    users: [],
    categories: [],
    movements: [],
    anomaliesMap: new Map(), // Map<id_movimiento, anomalyObject>
    activeTypeFilter: 'all',
    activeCategoryFilter: '',
    searchQuery: '',
    editingMovementId: null,
    // Auth State
    isAuthenticated: false,
    currentUser: null, // { id_usuario, nombre, email, moneda }
    sessionToken: null
};

// ==============================================================================
// 1. CLIENTE DE SERVICIOS API (Endpoints REST)
// ==============================================================================
const API = {
    // Detecta automáticamente la URL del servidor Flask si el frontend se abre como archivo local (file://) o puerto distinto (Live Server)
    baseUrl: (window.location.protocol === 'file:' || (window.location.port !== '5000' && window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'))
        ? 'http://127.0.0.1:5000' 
        : '',

    async request(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.message || `Error HTTP ${response.status}`);
            }
            return data;
        } catch (error) {
            console.error(`[API Error] en ${endpoint}:`, error);
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('No se pudo conectar al servidor backend. Asegúrate de que el servidor Flask esté corriendo (python backend/app.py).');
            }
            throw error;
        }
    },

    // Usuarios
    getUsers() {
        return this.request('/api/usuarios');
    },

    createUser(payload) {
        return this.request('/api/usuarios', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    // Categorías
    getCategories(userId, type = null) {
        let url = `/api/categorias?id_usuario=${userId}`;
        if (type) url += `&tipo=${type}`;
        return this.request(url);
    },

    createCategory(payload) {
        return this.request('/api/categorias', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    // Movimientos
    getMovements(userId, month = null, type = null, categoryId = null, search = '') {
        const params = new URLSearchParams({ id_usuario: userId });
        if (month) params.append('mes', month);
        if (type && type !== 'all') params.append('tipo', type);
        if (categoryId) params.append('id_categoria', categoryId);
        if (search) params.append('busqueda', search);
        return this.request(`/api/movimientos?${params.toString()}`);
    },

    createMovement(payload) {
        return this.request('/api/movimientos', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    updateMovement(id, payload) {
        return this.request(`/api/movimientos/${id}`, {
            method: 'PUT',
            body: JSON.stringify(payload)
        });
    },

    deleteMovement(id) {
        return this.request(`/api/movimientos/${id}`, {
            method: 'DELETE'
        });
    },

    // Resumen Ejecutivo
    getSummary(userId, month = null) {
        let url = `/api/resumen?id_usuario=${userId}`;
        if (month) url += `&mes=${month}`;
        return this.request(url);
    },

    // Analítica y Machine Learning
    getPrediction(userId) {
        return this.request(`/api/analitica/prediccion?id_usuario=${userId}`);
    },

    getAnomalies(userId, umbral = 2.0) {
        return this.request(`/api/analitica/anomalias?id_usuario=${userId}&umbral=${umbral}`);
    },

    getHistoricalTrend(userId) {
        return this.request(`/api/analitica/historico-comparativo?id_usuario=${userId}`);
    },

    // Autenticación
    login(email, password) {
        return this.request('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
    },

    register(payload) {
        return this.request('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify(payload)
        });
    },

    getMe(userId) {
        return this.request(`/api/auth/me?id_usuario=${userId}`);
    },

    logout() {
        return this.request('/api/auth/logout', { method: 'POST' });
    }
};

// ==============================================================================
// 2. UTILITARIOS DE FORMATO Y UI
// ==============================================================================
const UI = {
    formatCurrency(amount) {
        const val = parseFloat(amount) || 0;
        return new Intl.NumberFormat('es-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2
        }).format(val);
    },

    formatDate(dateStr) {
        if (!dateStr) return '';
        const [year, month, day] = dateStr.split('-');
        return `${day}/${month}/${year}`;
    },

    showToast(message, type = 'success') {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        let iconName = 'check-circle';
        if (type === 'error') iconName = 'alert-triangle';
        if (type === 'warning') iconName = 'alert-circle';

        toast.innerHTML = `
            <i data-lucide="${iconName}" style="width: 18px; height: 18px; flex-shrink: 0;"></i>
            <span>${message}</span>
        `;

        container.appendChild(toast);
        if (window.lucide) lucide.createIcons();

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    },

    refreshIcons() {
        if (window.lucide) {
            lucide.createIcons();
        }
    }
};

// ==============================================================================
// 3. CONTROLADOR DE AUTENTICACIÓN
// ==============================================================================

const Auth = {
    STORAGE_KEY: 'fiskal_session',

    /** Guarda la sesión del usuario en localStorage */
    saveSession(userData, token) {
        const session = {
            user: userData,
            token: token,
            timestamp: Date.now()
        };
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(session));
        AppState.isAuthenticated = true;
        AppState.currentUser = userData;
        AppState.activeUserId = userData.id_usuario;
        AppState.sessionToken = token;
    },

    /** Recupera la sesión guardada */
    loadSession() {
        try {
            const raw = localStorage.getItem(this.STORAGE_KEY);
            if (!raw) return null;
            const session = JSON.parse(raw);
            // Expiración: 7 días
            if (Date.now() - session.timestamp > 7 * 24 * 60 * 60 * 1000) {
                this.clearSession();
                return null;
            }
            return session;
        } catch {
            this.clearSession();
            return null;
        }
    },

    /** Borra la sesión */
    clearSession() {
        localStorage.removeItem(this.STORAGE_KEY);
        AppState.isAuthenticated = false;
        AppState.currentUser = null;
        AppState.activeUserId = null;
        AppState.sessionToken = null;
    },

    /** Muestra el overlay de autenticación */
    showAuthScreen() {
        const overlay = document.getElementById('authOverlay');
        if (overlay) overlay.classList.remove('hidden');
        UI.refreshIcons();
    },

    /** Oculta el overlay de autenticación */
    hideAuthScreen() {
        const overlay = document.getElementById('authOverlay');
        if (overlay) overlay.classList.add('hidden');
    },

    /** Actualiza el perfil de usuario en la barra de navegación */
    updateNavProfile(user) {
        const avatar = document.getElementById('navUserAvatar');
        const name = document.getElementById('navUserName');
        const email = document.getElementById('navUserEmail');

        if (avatar && user.nombre) {
            const initials = user.nombre.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
            avatar.textContent = initials;
        }
        if (name) name.textContent = user.nombre || 'Usuario';
        if (email) email.textContent = user.email || '';
    },

    /** Muestra un error en los formularios de auth */
    showError(formType, message) {
        const errorEl = document.getElementById(formType === 'login' ? 'loginError' : 'registerError');
        const textEl = document.getElementById(formType === 'login' ? 'loginErrorText' : 'registerErrorText');
        if (errorEl && textEl) {
            textEl.textContent = message;
            errorEl.classList.add('visible');
            UI.refreshIcons();
        }
    },

    /** Oculta los errores de auth */
    hideError(formType) {
        const errorEl = document.getElementById(formType === 'login' ? 'loginError' : 'registerError');
        if (errorEl) errorEl.classList.remove('visible');
    },

    /** Procesa el login exitoso */
    async onLoginSuccess(data) {
        this.saveSession(data.usuario, data.token);
        this.updateNavProfile(data.usuario);
        this.hideAuthScreen();

        initDefaultDates();
        await refreshDashboard();
        UI.showToast(`¡Bienvenido, ${data.usuario.nombre}!`, 'success');
    },

    /** Cierra la sesión */
    async handleLogout() {
        try {
            await API.logout();
        } catch (e) { /* silencioso */ }
        this.clearSession();
        this.showAuthScreen();
        UI.showToast('Sesión cerrada correctamente', 'success');

        // Limpiar formularios
        const formLogin = document.getElementById('formLogin');
        const formRegister = document.getElementById('formRegister');
        if (formLogin) formLogin.reset();
        if (formRegister) formRegister.reset();
        this.hideError('login');
        this.hideError('register');
    }
};

// ==============================================================================
// 4. CONTROLADOR Y FLUJO DE DATOS
// ==============================================================================

/**
 * Inicialización de la aplicación
 */
document.addEventListener('DOMContentLoaded', async () => {
    setupAuthListeners();
    setupEventListeners();
    UI.refreshIcons();

    // Verificar sesión existente
    const session = Auth.loadSession();
    if (session && session.user) {
        AppState.isAuthenticated = true;
        AppState.currentUser = session.user;
        AppState.activeUserId = session.user.id_usuario;
        AppState.sessionToken = session.token;

        Auth.updateNavProfile(session.user);
        Auth.hideAuthScreen();
        initDefaultDates();
        await refreshDashboard();
    } else {
        Auth.showAuthScreen();
    }
});

/**
 * Configura fecha del mes actual por defecto (dinámico a la fecha de hoy)
 */
function initDefaultDates() {
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonthNum = String(now.getMonth() + 1).padStart(2, '0');
    const currentDay = String(now.getDate()).padStart(2, '0');
    
    // Mes actual en formato YYYY-MM
    const currentYearMonth = `${currentYear}-${currentMonthNum}`;
    const todayFormatted = `${currentYear}-${currentMonthNum}-${currentDay}`;

    AppState.activeMonth = currentYearMonth;

    const monthInput = document.getElementById('monthSelector');
    if (monthInput) {
        monthInput.value = currentYearMonth;
    }

    const movFechaInput = document.getElementById('movFecha');
    if (movFechaInput) {
        movFechaInput.value = todayFormatted;
    }
}

/**
 * Recarga completa reactiva del Dashboard para el usuario y mes activo
 */
async function refreshDashboard() {
    if (!AppState.activeUserId) return;

    try {
        // Ejecutar peticiones en paralelo para alto rendimiento
        const [categoriesRes, summaryRes, predictionRes, anomaliesRes, trendRes] = await Promise.allSettled([
            API.getCategories(AppState.activeUserId),
            API.getSummary(AppState.activeUserId, AppState.activeMonth),
            API.getPrediction(AppState.activeUserId),
            API.getAnomalies(AppState.activeUserId, 2.0),
            API.getHistoricalTrend(AppState.activeUserId)
        ]);

        // 1. Procesar Categorías
        if (categoriesRes.status === 'fulfilled') {
            AppState.categories = categoriesRes.value.data || [];
            renderCategoryFilterDropdown();
        }

        // 2. Procesar Detección de Anomalías (para cruzar con la tabla)
        AppState.anomaliesMap.clear();
        if (anomaliesRes.status === 'fulfilled') {
            const anomData = anomaliesRes.value.data || {};
            const anomList = anomData.anomalias || [];
            anomList.forEach(a => AppState.anomaliesMap.set(a.id_movimiento, a));
            renderAnomaliesBanner(anomList);
        }

        // 3. Procesar Resumen Ejecutivo y Gráfico de Dona
        if (summaryRes.status === 'fulfilled') {
            const sData = summaryRes.value;
            renderSummaryCards(sData.resumen);
            
            // Actualizar período si la API detectó uno más reciente
            if (sData.periodo && sData.periodo !== AppState.activeMonth) {
                AppState.activeMonth = sData.periodo;
                const mInput = document.getElementById('monthSelector');
                if (mInput) mInput.value = AppState.activeMonth;
            }

            // Gráfico de Dona
            ChartsManager.renderCategoryDoughnut('categoryDoughnutChart', sData.distribucion_gastos || []);
        }

        // 4. Procesar Predicción con Regresión Lineal
        if (predictionRes.status === 'fulfilled') {
            renderPredictionCard(predictionRes.value);
        }

        // 5. Procesar Histórico y Gráfico de Tendencias
        if (trendRes.status === 'fulfilled') {
            ChartsManager.renderMonthlyTrendChart('monthlyTrendChart', trendRes.value.data || []);
        }

        // 6. Cargar Tabla de Movimientos
        await loadMovementsTable();

        UI.refreshIcons();
    } catch (err) {
        console.error('Error al actualizar el dashboard:', err);
        UI.showToast('Error al refrescar componentes del dashboard', 'error');
    }
}

/**
 * Renderiza las tarjetas KPI de Resumen
 */
function renderSummaryCards(resumen = {}) {
    const incEl = document.getElementById('kpiIncomeValue');
    const expEl = document.getElementById('kpiExpenseValue');
    const balEl = document.getElementById('kpiBalanceValue');
    const savEl = document.getElementById('kpiSavingsRate');
    
    const incDiffEl = document.getElementById('kpiIncomeDiff');
    const expDiffEl = document.getElementById('kpiExpenseDiff');

    const ingresos = resumen.ingresos || 0;
    const gastos = resumen.gastos || 0;
    const balance = resumen.balance || 0;
    const tasaAhorro = resumen.tasa_ahorro_pct || 0;

    if (incEl) incEl.textContent = UI.formatCurrency(ingresos);
    if (expEl) expEl.textContent = UI.formatCurrency(gastos);
    
    if (balEl) {
        balEl.textContent = UI.formatCurrency(balance);
        balEl.style.color = balance >= 0 ? 'var(--color-income)' : 'var(--color-expense)';
    }

    if (savEl) {
        savEl.textContent = `Ahorro: ${tasaAhorro}%`;
        savEl.className = `badge ${tasaAhorro >= 20 ? 'badge-savings' : 'badge-neutral'}`;
    }

    // Comparativa con mes anterior
    if (resumen.comparativa) {
        const difInc = resumen.comparativa.dif_ingresos_pct || 0;
        const difExp = resumen.comparativa.dif_gastos_pct || 0;

        if (incDiffEl) {
            incDiffEl.className = `kpi-trend ${difInc >= 0 ? 'trend-up' : 'trend-down'}`;
            incDiffEl.innerHTML = `
                <i data-lucide="${difInc >= 0 ? 'arrow-up-right' : 'arrow-down-right'}" class="trend-icon"></i>
                <span>${Math.abs(difInc)}% vs mes anterior</span>
            `;
        }

        if (expDiffEl) {
            expDiffEl.className = `kpi-trend ${difExp <= 0 ? 'trend-up' : 'trend-down'}`;
            expDiffEl.innerHTML = `
                <i data-lucide="${difExp > 0 ? 'arrow-up-right' : 'arrow-down-right'}" class="trend-icon"></i>
                <span>${difExp > 0 ? '+' : ''}${difExp}% vs mes anterior</span>
            `;
        }
    }
}

/**
 * Renderiza la tarjeta de Predicción del Próximo Mes (Scikit-Learn)
 */
function renderPredictionCard(predRes) {
    const predValEl = document.getElementById('kpiPredictionValue');
    const predTextEl = document.getElementById('kpiPredictionText');

    if (!predRes) return;

    if (predRes.status === 'warning') {
        if (predValEl) predValEl.textContent = 'Pendiente';
        if (predTextEl) {
            predTextEl.textContent = `${predRes.meses_disponibles}/${predRes.meses_requeridos} meses registrados para predicción`;
        }
        return;
    }

    const data = predRes.data;
    if (data && data.gasto_predicho !== undefined) {
        if (predValEl) predValEl.textContent = UI.formatCurrency(data.gasto_predicho);
        if (predTextEl) {
            const slope = data.metricas?.pendiente || 0;
            const sign = slope >= 0 ? '+' : '';
            predTextEl.textContent = `Proyección (${data.proximo_periodo}): ${sign}$${slope}/mes`;
        }
    }
}

/**
 * Renderiza el banner de alertas de anomalías (Z-Score >= 2.0)
 */
function renderAnomaliesBanner(anomalias = []) {
    const section = document.getElementById('anomaliesSection');
    const list = document.getElementById('anomaliesList');
    const counter = document.getElementById('anomalyCounterBadge');

    if (!section || !list) return;

    if (anomalias.length === 0) {
        section.classList.add('hidden');
        list.innerHTML = '';
        return;
    }

    section.classList.remove('hidden');
    if (counter) counter.textContent = `${anomalias.length} detectada(s)`;

    list.innerHTML = anomalias.map(a => `
        <div class="anomaly-item-card">
            <div class="anomaly-item-top">
                <div class="anomaly-category-tag">
                    <span class="anomaly-cat-dot" style="background: ${a.color || '#ec4899'};"></span>
                    <span>${a.categoria}</span>
                </div>
                <span class="anomaly-amount">${UI.formatCurrency(a.monto)}</span>
            </div>
            <div class="anomaly-description">
                <strong>${a.descripcion}</strong> &bull; ${UI.formatDate(a.fecha)}
            </div>
            <div class="anomaly-metrics-pill">
                <span>Z-Score: <strong class="anomaly-z-val">${a.z_score}σ</strong></span>
                <span>Desviación: <strong>+${a.porcentaje_sobre_media}%</strong></span>
            </div>
            <p class="anomaly-msg">${a.mensaje}</p>
        </div>
    `).join('');
}

/**
 * Carga y renderiza la tabla de transacciones
 */
async function loadMovementsTable() {
    const tbody = document.getElementById('movementsTableBody');
    const counter = document.getElementById('movementsCounter');
    if (!tbody) return;

    try {
        const res = await API.getMovements(
            AppState.activeUserId,
            AppState.activeMonth,
            AppState.activeTypeFilter,
            AppState.activeCategoryFilter,
            AppState.searchQuery
        );

        AppState.movements = res.data || [];
        if (counter) counter.textContent = `${AppState.movements.length} registro(s)`;

        if (AppState.movements.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center py-6 text-muted">
                        No se encontraron movimientos registrados para este período o filtro.
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = AppState.movements.map(m => {
            const isAnomaly = AppState.anomaliesMap.has(m.id_movimiento);
            const anomalyData = isAnomaly ? AppState.anomaliesMap.get(m.id_movimiento) : null;
            const isIncome = m.tipo === 'ingreso';

            return `
                <tr class="${isAnomaly ? 'row-anomalous' : ''}">
                    <td>${UI.formatDate(m.fecha)}</td>
                    <td><strong>${escapeHtml(m.descripcion)}</strong></td>
                    <td>
                        <span class="category-badge">
                            <span class="cat-indicator" style="background: ${m.categoria_color || '#6366f1'};"></span>
                            ${escapeHtml(m.categoria)}
                        </span>
                    </td>
                    <td>
                        <span class="text-muted" style="text-transform: capitalize;">
                            ${m.metodo_pago.replace('_', ' ')}
                        </span>
                    </td>
                    <td class="text-right ${isIncome ? 'amount-income' : 'amount-expense'}">
                        ${isIncome ? '+' : '-'}${UI.formatCurrency(m.monto)}
                    </td>
                    <td class="text-center">
                        ${isAnomaly ? `
                            <span class="anomaly-alert-chip" title="${anomalyData?.mensaje || 'Gasto atípico detectado por Z-score'}">
                                <i data-lucide="alert-triangle" style="width: 12px; height: 12px;"></i>
                                Z=${anomalyData?.z_score || '2.0'}σ
                            </span>
                        ` : `
                            <span class="badge badge-neutral">Normal</span>
                        `}
                    </td>
                    <td class="text-right">
                        <div class="table-actions">
                            <button class="btn-action btn-edit" onclick="handleEditMovement(${m.id_movimiento})" title="Editar Movimiento">
                                <i data-lucide="edit-3" style="width: 15px; height: 15px;"></i>
                            </button>
                            <button class="btn-action btn-delete" onclick="handleDeleteMovement(${m.id_movimiento})" title="Eliminar Movimiento">
                                <i data-lucide="trash-2" style="width: 15px; height: 15px;"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        UI.refreshIcons();
    } catch (err) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-6 text-muted">
                    Error al cargar las transacciones.
                </td>
            </tr>
        `;
    }
}

/**
 * Llena el selector de categorías del filtro superior
 */
function renderCategoryFilterDropdown() {
    const filterSelect = document.getElementById('categoryFilter');
    if (!filterSelect) return;

    const currentVal = filterSelect.value;
    filterSelect.innerHTML = '<option value="">Todas las Categorías</option>';

    AppState.categories.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.id_categoria;
        opt.textContent = `${c.tipo === 'ingreso' ? '➕' : '➖'} ${c.nombre}`;
        filterSelect.appendChild(opt);
    });

    filterSelect.value = currentVal;
}

/**
 * Llena el selector de categorías del modal según el tipo seleccionado ('gasto' / 'ingreso')
 */
function populateModalCategories(tipoSeleccionado = 'gasto') {
    const catSelect = document.getElementById('movCategoria');
    if (!catSelect) return;

    const filtered = AppState.categories.filter(c => c.tipo === tipoSeleccionado);
    catSelect.innerHTML = '<option value="" disabled selected>Seleccione una categoría</option>';

    filtered.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.id_categoria;
        opt.textContent = c.nombre;
        catSelect.appendChild(opt);
    });
}

// ==============================================================================
// 4. GESTIÓN DE MODALES Y FORMULARIOS
// ==============================================================================

/**
 * Abre el modal para registrar un nuevo movimiento
 */
function openCreateMovementModal() {
    AppState.editingMovementId = null;
    document.getElementById('modalMovementTitle').textContent = 'Registrar Movimiento';
    document.getElementById('btnSaveMovementText').textContent = 'Guardar Movimiento';
    document.getElementById('formMovement').reset();
    document.getElementById('movId').value = '';

    // Marcar gasto por defecto
    const radioGasto = document.getElementById('typeGasto');
    if (radioGasto) radioGasto.checked = true;
    populateModalCategories('gasto');

    document.getElementById('movFecha').value = new Date().toISOString().split('T')[0];
    document.getElementById('modalMovement').classList.remove('hidden');
    UI.refreshIcons();
}

/**
 * Prepara y abre el modal para editar un movimiento existente
 */
window.handleEditMovement = async function(id) {
    try {
        const res = await API.request(`/api/movimientos/${id}`);
        const m = res.data;
        if (!m) return;

        AppState.editingMovementId = id;
        document.getElementById('modalMovementTitle').textContent = 'Editar Movimiento';
        document.getElementById('btnSaveMovementText').textContent = 'Actualizar Movimiento';

        document.getElementById('movId').value = m.id_movimiento;
        document.getElementById('movMonto').value = m.monto;
        document.getElementById('movFecha').value = m.fecha;
        document.getElementById('movDescripcion').value = m.descripcion;
        document.getElementById('movMetodoPago').value = m.metodo_pago;

        if (m.tipo === 'ingreso') {
            document.getElementById('typeIngreso').checked = true;
            populateModalCategories('ingreso');
        } else {
            document.getElementById('typeGasto').checked = true;
            populateModalCategories('gasto');
        }

        document.getElementById('movCategoria').value = m.id_categoria;
        document.getElementById('modalMovement').classList.remove('hidden');
        UI.refreshIcons();
    } catch (err) {
        UI.showToast('No se pudo cargar la transacción para edición', 'error');
    }
};

/**
 * Elimina una transacción con confirmación
 */
window.handleDeleteMovement = async function(id) {
    if (!confirm('¿Estás seguro de eliminar este registro de movimiento?')) return;

    try {
        await API.deleteMovement(id);
        UI.showToast('Movimiento eliminado correctamente', 'success');
        await refreshDashboard();
    } catch (err) {
        UI.showToast(err.message || 'Error al eliminar movimiento', 'error');
    }
};

/**
 * Configuración de escuchas de eventos (Event Listeners)
 */
function setupEventListeners() {

    // 2. Selector de Mes
    const monthSelect = document.getElementById('monthSelector');
    if (monthSelect) {
        monthSelect.addEventListener('change', async (e) => {
            AppState.activeMonth = e.target.value;
            await refreshDashboard();
        });
    }

    // 3. Botón de Nuevo Movimiento
    const btnOpenMov = document.getElementById('btnOpenNewMovement');
    if (btnOpenMov) btnOpenMov.addEventListener('click', openCreateMovementModal);

    // Cerrar Modal Movimiento
    const btnCloseMov = document.getElementById('btnCloseMovementModal');
    const btnCancelMov = document.getElementById('btnCancelMovement');
    if (btnCloseMov) btnCloseMov.addEventListener('click', () => document.getElementById('modalMovement').classList.add('hidden'));
    if (btnCancelMov) btnCancelMov.addEventListener('click', () => document.getElementById('modalMovement').classList.add('hidden'));

    // Switch de Tipo en Modal Movimiento
    const radioGasto = document.getElementById('typeGasto');
    const radioIngreso = document.getElementById('typeIngreso');
    if (radioGasto) radioGasto.addEventListener('change', () => populateModalCategories('gasto'));
    if (radioIngreso) radioIngreso.addEventListener('change', () => populateModalCategories('ingreso'));

    // Guardar / Actualizar Movimiento
    const formMov = document.getElementById('formMovement');
    if (formMov) {
        formMov.addEventListener('submit', async (e) => {
            e.preventDefault();
            const id = document.getElementById('movId').value;
            const tipo = document.querySelector('input[name="movTipo"]:checked')?.value || 'gasto';
            const id_categoria = document.getElementById('movCategoria').value;
            const monto = document.getElementById('movMonto').value;
            const fecha = document.getElementById('movFecha').value;
            const descripcion = document.getElementById('movDescripcion').value.trim();
            const metodo_pago = document.getElementById('movMetodoPago').value;

            if (!id_categoria) {
                UI.showToast('Por favor selecciona una categoría', 'warning');
                return;
            }

            if (!monto || parseFloat(monto) <= 0) {
                UI.showToast('El monto debe ser mayor a 0', 'warning');
                return;
            }

            if (!descripcion) {
                UI.showToast('Ingresa una descripción para el movimiento', 'warning');
                return;
            }

            const payload = {
                id_usuario: AppState.activeUserId,
                id_categoria: parseInt(id_categoria),
                monto: parseFloat(monto),
                tipo,
                fecha,
                descripcion,
                metodo_pago
            };

            try {
                if (id) {
                    await API.updateMovement(id, payload);
                    UI.showToast('Movimiento actualizado con éxito', 'success');
                } else {
                    await API.createMovement(payload);
                    UI.showToast('Movimiento registrado con éxito', 'success');
                }
                document.getElementById('modalMovement').classList.add('hidden');
                await refreshDashboard();
            } catch (err) {
                UI.showToast(err.message || 'Error al guardar movimiento', 'error');
            }
        });
    }

    // 4. Modal de Categoría
    const btnOpenCat = document.getElementById('btnOpenNewCategory');
    if (btnOpenCat) {
        btnOpenCat.addEventListener('click', () => {
            document.getElementById('formCategory').reset();
            document.getElementById('modalCategory').classList.remove('hidden');
            UI.refreshIcons();
        });
    }

    const btnCloseCat = document.getElementById('btnCloseCategoryModal');
    const btnCancelCat = document.getElementById('btnCancelCategory');
    if (btnCloseCat) btnCloseCat.addEventListener('click', () => document.getElementById('modalCategory').classList.add('hidden'));
    if (btnCancelCat) btnCancelCat.addEventListener('click', () => document.getElementById('modalCategory').classList.add('hidden'));

    const catColorInput = document.getElementById('catColor');
    if (catColorInput) {
        catColorInput.addEventListener('input', (e) => {
            const lbl = document.getElementById('colorHexLabel');
            if (lbl) lbl.textContent = e.target.value;
        });
    }

    const formCat = document.getElementById('formCategory');
    if (formCat) {
        formCat.addEventListener('submit', async (e) => {
            e.preventDefault();
            const nombre = document.getElementById('catNombre').value.trim();
            const tipo = document.getElementById('catTipo').value;
            const color = document.getElementById('catColor').value;

            if (!nombre) {
                UI.showToast('Ingresa el nombre de la categoría', 'warning');
                return;
            }

            try {
                await API.createCategory({
                    nombre,
                    tipo,
                    color,
                    icono: 'tag',
                    id_usuario: AppState.activeUserId
                });
                UI.showToast('Categoría creada exitosamente', 'success');
                document.getElementById('modalCategory').classList.add('hidden');
                await refreshDashboard();
            } catch (err) {
                UI.showToast(err.message || 'Error al crear categoría', 'error');
            }
        });
    }

    // 5. Botón de Logout
    const btnLogout = document.getElementById('btnLogout');
    if (btnLogout) {
        btnLogout.addEventListener('click', () => Auth.handleLogout());
    }

    // 6. Filtros de la Tabla
    const searchInput = document.getElementById('tableSearchInput');
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                AppState.searchQuery = e.target.value.trim();
                loadMovementsTable();
            }, 300);
        });
    }

    const filterPills = document.querySelectorAll('.filter-pill');
    filterPills.forEach(pill => {
        pill.addEventListener('click', () => {
            filterPills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            AppState.activeTypeFilter = pill.dataset.type;
            loadMovementsTable();
        });
    });

    const catFilter = document.getElementById('categoryFilter');
    if (catFilter) {
        catFilter.addEventListener('change', (e) => {
            AppState.activeCategoryFilter = e.target.value;
            loadMovementsTable();
        });
    }
}

/**
 * Escapa strings para evitar inyección en HTML
 */
function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// ==============================================================================
// SISTEMA DE AUTENTICACIÓN - Event Listeners
// ==============================================================================

/**
 * Configura todos los listeners de la pantalla de autenticación
 */
function setupAuthListeners() {
    // 1. Tabs Login / Registro
    const tabLogin = document.getElementById('tabLogin');
    const tabRegister = document.getElementById('tabRegister');
    const panelLogin = document.getElementById('panelLogin');
    const panelRegister = document.getElementById('panelRegister');

    if (tabLogin && tabRegister) {
        tabLogin.addEventListener('click', () => {
            tabLogin.classList.add('active');
            tabRegister.classList.remove('active');
            if (panelLogin) panelLogin.classList.add('active');
            if (panelRegister) panelRegister.classList.remove('active');
            Auth.hideError('login');
            Auth.hideError('register');
            UI.refreshIcons();
        });

        tabRegister.addEventListener('click', () => {
            tabRegister.classList.add('active');
            tabLogin.classList.remove('active');
            if (panelRegister) panelRegister.classList.add('active');
            if (panelLogin) panelLogin.classList.remove('active');
            Auth.hideError('login');
            Auth.hideError('register');
            UI.refreshIcons();
        });
    }

    // 2. Botones de mostrar/ocultar contraseña
    document.querySelectorAll('.btn-toggle-pw').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.dataset.target;
            const input = document.getElementById(targetId);
            if (!input) return;

            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';

            // Cambiar icono
            const icon = btn.querySelector('i');
            if (icon) {
                icon.setAttribute('data-lucide', isPassword ? 'eye-off' : 'eye');
                UI.refreshIcons();
            }
        });
    });

    // 3. Indicador de fuerza de contraseña en Registro
    const regPasswordInput = document.getElementById('regPassword');
    const strengthBar = document.getElementById('regPasswordStrength');

    if (regPasswordInput && strengthBar) {
        regPasswordInput.addEventListener('input', (e) => {
            const pw = e.target.value;
            strengthBar.className = 'password-strength-bar';

            if (pw.length === 0) {
                strengthBar.className = 'password-strength-bar';
                return;
            }

            let score = 0;
            if (pw.length >= 6) score++;
            if (pw.length >= 10) score++;
            if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score++;
            if (/[0-9]/.test(pw)) score++;
            if (/[^A-Za-z0-9]/.test(pw)) score++;

            if (score <= 2) {
                strengthBar.classList.add('weak');
            } else if (score <= 3) {
                strengthBar.classList.add('medium');
            } else {
                strengthBar.classList.add('strong');
            }
        });
    }

    // 4. Formulario de LOGIN
    const formLogin = document.getElementById('formLogin');
    if (formLogin) {
        formLogin.addEventListener('submit', async (e) => {
            e.preventDefault();
            Auth.hideError('login');

            const email = document.getElementById('loginEmail').value.trim();
            const password = document.getElementById('loginPassword').value;
            const btnLogin = document.getElementById('btnLogin');

            if (!email || !password) {
                Auth.showError('login', 'Por favor completa todos los campos');
                return;
            }

            // Deshabilitar botón durante la petición
            if (btnLogin) {
                btnLogin.disabled = true;
                btnLogin.innerHTML = '<i data-lucide="loader-2" style="animation: spin 1s linear infinite;"></i> Verificando...';
                UI.refreshIcons();
            }

            try {
                const res = await API.login(email, password);
                if (res.status === 'success' && res.data) {
                    await Auth.onLoginSuccess(res.data);
                } else {
                    Auth.showError('login', res.message || 'Credenciales incorrectas');
                }
            } catch (err) {
                Auth.showError('login', err.message || 'Error al iniciar sesión');
            } finally {
                if (btnLogin) {
                    btnLogin.disabled = false;
                    btnLogin.innerHTML = '<i data-lucide="log-in"></i> Iniciar Sesión';
                    UI.refreshIcons();
                }
            }
        });
    }

    // 5. Formulario de REGISTRO
    const formRegister = document.getElementById('formRegister');
    if (formRegister) {
        formRegister.addEventListener('submit', async (e) => {
            e.preventDefault();
            Auth.hideError('register');

            const nombre = document.getElementById('regName').value.trim();
            const email = document.getElementById('regEmail').value.trim();
            const password = document.getElementById('regPassword').value;
            const moneda = document.getElementById('regCurrency').value;
            const btnRegister = document.getElementById('btnRegister');

            if (!nombre || nombre.length < 2) {
                Auth.showError('register', 'El nombre completo es obligatorio (mínimo 2 caracteres)');
                return;
            }

            const emailRegex = /^[\w\.-]+@[\w\.-]+\.\w+$/;
            if (!email || !emailRegex.test(email)) {
                Auth.showError('register', 'Por favor ingresa un correo electrónico válido');
                return;
            }

            if (!password || password.length < 6) {
                Auth.showError('register', 'La contraseña debe tener al menos 6 caracteres');
                return;
            }

            // Deshabilitar botón durante la petición
            if (btnRegister) {
                btnRegister.disabled = true;
                btnRegister.innerHTML = '<i data-lucide="loader-2" style="animation: spin 1s linear infinite;"></i> Creando cuenta...';
                UI.refreshIcons();
            }

            try {
                const res = await API.register({ nombre, email, password, moneda });
                if (res.status === 'success' && res.data) {
                    await Auth.onLoginSuccess(res.data);
                } else {
                    Auth.showError('register', res.message || 'Error al crear la cuenta');
                }
            } catch (err) {
                Auth.showError('register', err.message || 'Error al registrar usuario');
            } finally {
                if (btnRegister) {
                    btnRegister.disabled = false;
                    btnRegister.innerHTML = '<i data-lucide="user-plus"></i> Crear Mi Cuenta';
                    UI.refreshIcons();
                }
            }
        });
    }
}

