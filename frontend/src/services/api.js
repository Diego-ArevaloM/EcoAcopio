const BASE = "http://localhost:8000/api";

export const Api = {
  getToken: () => localStorage.getItem("eco_token"),
  getUser: () => { try { return JSON.parse(localStorage.getItem("eco_user")); } catch { return null; } },
  setToken: (t, u) => { localStorage.setItem("eco_token", t); localStorage.setItem("eco_user", JSON.stringify(u)); },
  clearToken: () => { localStorage.removeItem("eco_token"); localStorage.removeItem("eco_user"); },

  headers: () => ({
    "Content-Type": "application/json",
    ...(localStorage.getItem("eco_token") ? { Authorization: `Bearer ${localStorage.getItem("eco_token")}` } : {}),
  }),

  req: async (method, path, body) => {
    const res = await fetch(`${BASE}${path}`, {
      method, headers: Api.headers(),
      ...(body ? { body: JSON.stringify(body) } : {}),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || data.message || "Error en la solicitud");
    return data;
  },

  login: async (email, password) => {
    const res = await fetch(`${BASE}/auth/login`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Credenciales incorrectas");
    Api.setToken(data.access_token, data.user);
    return data.user;
  },
  
  logout: async () => {
    try { await Api.req("POST", "/auth/logout"); } catch (e) { console.error(e); }
    Api.clearToken();
  },

  me: () => Api.req("GET", "/auth/me"),
  materiales: (soloActivos = true) => Api.req("GET", `/materiales${soloActivos ? "?activos=true" : ""}`),
  crearMaterial: (body) => Api.req("POST", "/materiales", body),
  actualizarMaterial: (id, body) => Api.req("PUT", `/materiales/${id}`, body),
  toggleMaterial: (id) => Api.req("POST", `/materiales/${id}/toggle`),
  proveedores: () => Api.req("GET", "/proveedores"),
  crearProveedor: (body) => Api.req("POST", "/proveedores", body),
  actualizarProveedor: (id, body) => Api.req("PUT", `/proveedores/${id}`, body),
  pesajes: (qs = "") => Api.req("GET", `/pesajes${qs}`),
  registrarPesaje: (body) => Api.req("POST", "/pesajes", body),
  inventario: (buscar = "") => Api.req("GET", `/inventario${buscar ? `?search=${buscar}` : ""}`),
  dashboard: () => Api.req("GET", "/dashboard"),
  reporte: (mes, year) => Api.req("GET", `/reportes?mes=${mes}&year=${year}`),
  exportarCSV: (mes, year) => `${BASE}/reportes/export?mes=${mes}&year=${year}&token=${Api.getToken()}`,
  auditoria: (limit = 100) => Api.req("GET", `/auditoria?limit=${limit}`),
  analizarIA: (body) => Api.req("POST", "/scanner/analizar", body),
};