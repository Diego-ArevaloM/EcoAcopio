/**
 * EcoAcopio ERP — API Client
 * Conecta el frontend con el backend FastAPI.
 * Configurar BASE_URL según el entorno.
 */

// En producción, si el frontend y backend están en el mismo servidor, usa ''
// En desarrollo local usa 'http://localhost:8000'
const BASE_URL = window.ECOACOPIO_API_URL || '';

const Api = {
  // ── TOKEN ──────────────────────────────────────────────────────────────────
  getToken() { return localStorage.getItem('ecoaCopio_token'); },
  setToken(t) { localStorage.setItem('ecoaCopio_token', t); },
  clearToken() { localStorage.removeItem('ecoaCopio_token'); localStorage.removeItem('ecoaCopio_user'); },

  getUser() {
    try { return JSON.parse(localStorage.getItem('ecoaCopio_user') || 'null'); }
    catch { return null; }
  },
  setUser(u) { localStorage.setItem('ecoaCopio_user', JSON.stringify(u)); },

  // ── FETCH BASE ─────────────────────────────────────────────────────────────
  async _fetch(path, options = {}) {
    const token = this.getToken();
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const resp = await fetch(`${BASE_URL}${path}`, { ...options, headers });

    if (resp.status === 401) {
      this.clearToken();
      location.reload();
      throw new Error('Sesión expirada');
    }

    const ct = resp.headers.get('content-type') || '';
    const data = ct.includes('application/json') ? await resp.json() : await resp.text();

    if (!resp.ok) {
      const msg = typeof data === 'object'
        ? (data.detail?.message || data.detail || JSON.stringify(data))
        : data;
      const err = new Error(msg);
      err.data = data;
      err.status = resp.status;
      throw err;
    }
    return data;
  },

  async _fetchForm(path, formData) {
    const token = this.getToken();
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const resp = await fetch(`${BASE_URL}${path}`, { method: 'POST', headers, body: formData });
    if (!resp.ok) {
      const data = await resp.json().catch(() => ({}));
      throw new Error(data.detail || 'Error en la solicitud');
    }
    return resp.json();
  },

  get: (p, o={})  => Api._fetch(p, { method: 'GET', ...o }),
  post: (p, b, o={}) => Api._fetch(p, { method: 'POST', body: JSON.stringify(b), ...o }),
  put:  (p, b, o={}) => Api._fetch(p, { method: 'PUT',  body: JSON.stringify(b), ...o }),
  patch:(p, b={}, o={})=> Api._fetch(p, { method: 'PATCH', body: JSON.stringify(b), ...o }),
  del:  (p, o={}) => Api._fetch(p, { method: 'DELETE', ...o }),

  // ── AUTH ───────────────────────────────────────────────────────────────────
  async login(email, password) {
    const data = await this.post('/api/auth/login', { email, password });
    this.setToken(data.access_token);
    this.setUser(data.user);
    return data.user;
  },
  async logout() {
    try { await this.post('/api/auth/logout', {}); } catch {}
    this.clearToken();
  },
  me: () => Api.get('/api/auth/me'),

  // ── DASHBOARD ─────────────────────────────────────────────────────────────
  dashboardStats: () => Api.get('/api/dashboard/stats'),

  // ── PESAJES ───────────────────────────────────────────────────────────────
  pesajes: (params = '') => Api.get(`/api/pesajes/${params}`),
  crearPesaje: (body) => Api.post('/api/pesajes/', body),
  anularPesaje: (id, motivo) => Api.put(`/api/pesajes/${id}/anular`, { motivo }),

  // ── MATERIALES ────────────────────────────────────────────────────────────
  materiales: (soloActivos = false) => Api.get(`/api/materiales/?solo_activos=${soloActivos}`),
  crearMaterial: (body) => Api.post('/api/materiales/', body),
  actualizarMaterial: (id, body) => Api.put(`/api/materiales/${id}`, body),
  toggleMaterial: (id) => Api.patch(`/api/materiales/${id}/toggle`),
  categorias: () => Api.get('/api/materiales/categorias/'),

  // ── PROVEEDORES ───────────────────────────────────────────────────────────
  proveedores: () => Api.get('/api/proveedores/'),
  crearProveedor: (body) => Api.post('/api/proveedores/', body),
  actualizarProveedor: (id, body) => Api.put(`/api/proveedores/${id}`, body),
  eliminarProveedor: (id) => Api.del(`/api/proveedores/${id}`),

  // ── INVENTARIO ────────────────────────────────────────────────────────────
  inventario: (buscar = '') => Api.get(`/api/inventario/${buscar ? `?buscar=${buscar}` : ''}`),
  stockMaterial: (id) => Api.get(`/api/inventario/stock/${id}`),

  // ── REPORTES ──────────────────────────────────────────────────────────────
  reporte: (mes, año) => Api.get(`/api/reportes/?mes=${mes}&año=${año}`),
  cerrarMes: (mes, año) => Api.post('/api/reportes/cerrar', { mes, año }),
  exportarCSV: (mes, año) => `${BASE_URL}/api/reportes/exportar-csv?mes=${mes}&año=${año}`,

  // ── AUDITORÍA ─────────────────────────────────────────────────────────────
  auditoria: (limit=100) => Api.get(`/api/auditoria/?limit=${limit}`),

  // ── SCANNER IA ────────────────────────────────────────────────────────────
  async analizarMaterial(descripcion, archivoImagen) {
    const fd = new FormData();
    if (descripcion) fd.append('descripcion', descripcion);
    if (archivoImagen) fd.append('imagen', archivoImagen);
    return this._fetchForm('/api/scanner/analizar', fd);
  },
};
