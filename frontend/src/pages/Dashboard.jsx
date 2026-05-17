import { useState, useEffect } from "react";
import { Api } from "../services/api";

export default function DashboardPage({ app, onNav, showToast }) {
  const [dash, setDash] = useState(null);
  const [txs, setTxs] = useState([]);

  useEffect(() => {
    Api.dashboard().then(setDash).catch(() => {});
    Api.pesajes("?limit=8").then(d => setTxs(d.items || [])).catch(() => {});
  }, []);

  const date = new Date().toLocaleDateString("es-PE", { weekday: "long", year: "numeric", month: "long", day: "numeric" });
  const mats = app.materiales.filter(m => m.stock_kg > 0).slice(0, 6);
  const totalStock = app.materiales.reduce((s, m) => s + (m.stock_kg || 0), 0);
  const chartData = app.materiales.filter(m => m.stock_kg > 0).slice(0, 7);
  const maxKg = Math.max(...chartData.map(m => m.stock_kg), 1);

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Dashboard Operativo</h1>
        <p className="page-sub">{date}</p>
      </div>
      <div className="grid-4 mb-16">
        <div className="stat-card">
          <div className="stat-icon">⚖️</div>
          <div className="stat-label">PESAJES HOY</div>
          <div className="stat-value text-green">{dash?.pesajes_hoy ?? "—"}</div>
          <div className="stat-trend stat-neutral">registros</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">📦</div>
          <div className="stat-label">KG INGRESADOS HOY</div>
          <div className="stat-value text-blue">{dash?.kg_hoy?.toFixed(1) ?? "—"}</div>
          <div className="stat-trend stat-neutral">kg acumulados</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">👥</div>
          <div className="stat-label">PROVEEDORES ACTIVOS</div>
          <div className="stat-value text-amber">{app.proveedores.length}</div>
          <div className="stat-trend stat-neutral">registrados</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🏷️</div>
          <div className="stat-label">MATERIALES EN STOCK</div>
          <div className="stat-value">{app.materiales.filter(m => m.activo).length}</div>
          <div className="stat-trend stat-neutral">categorías activas</div>
        </div>
      </div>

      <div className="grid-21 mb-16">
        <div className="card">
          <div className="flex-between mb-16">
            <span className="card-title" style={{ marginBottom: 0 }}>Últimos Registros</span>
            <button className="btn btn-ghost btn-sm" onClick={() => onNav("pesaje")}>+ Nuevo</button>
          </div>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Material</th><th>Proveedor</th><th>Peso</th><th>Hora</th><th>Estado</th></tr></thead>
              <tbody>
                {txs.length === 0
                  ? <tr><td colSpan={5} style={{ textAlign: "center", color: "var(--text3)", padding: 24 }}>Sin registros aún</td></tr>
                  : txs.map(t => (
                    <tr key={t.id}>
                      <td><span className="main-cell">{t.emoji || "♻️"} {t.material}</span></td>
                      <td>{t.proveedor}</td>
                      <td className="mono" style={{ color: t.tipo === "entrada" ? "var(--green)" : "var(--red)" }}>
                        {t.tipo === "entrada" ? "+" : "−"}{parseFloat(t.peso_kg).toFixed(2)} kg
                      </td>
                      <td className="mono" style={{ fontSize: 12 }}>{new Date(t.registrado_en).toLocaleTimeString("es-PE", { hour: "2-digit", minute: "2-digit" })}</td>
                      <td><span className={`badge badge-${t.tipo === "entrada" ? "green" : "red"}`}>{t.tipo === "entrada" ? "Entrada" : "Salida"}</span></td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
        <div className="card">
          <div className="card-title">Stock por Material</div>
          <div className="chart-container">
            {chartData.length === 0
              ? <p style={{ fontSize: 13, color: "var(--text3)", margin: "auto" }}>Sin datos</p>
              : chartData.map((m, i) => {
                const pct = (m.stock_kg / maxKg) * 100;
                const colors = ["var(--green)", "var(--blue)", "var(--amber)", "var(--teal)", "var(--red)", "var(--green)", "var(--blue)"];
                return (
                  <div className="chart-bar-wrap" key={m.id}>
                    <div className="chart-bar-val">{m.stock_kg.toFixed(0)}</div>
                    <div style={{ flex: 1, display: "flex", alignItems: "flex-end", width: "100%" }}>
                      <div className="chart-bar" style={{ height: `${pct}%`, background: colors[i % colors.length], width: "100%" }} />
                    </div>
                    <div className="chart-bar-label">{m.emoji || "♻️"}</div>
                  </div>
                );
              })}
          </div>
          <div className="sep" />
          <div className="card-title">Alertas del Sistema</div>
          <div className="alert alert-info"><span className="alert-icon">ℹ️</span>Sistema iniciado correctamente. Todos los módulos operativos.</div>
        </div>
      </div>

      <div className="card">
        <div className="flex-between mb-16">
          <span className="card-title" style={{ marginBottom: 0 }}>Resumen de Inventario</span>
          <button className="btn btn-ghost btn-sm" onClick={() => onNav("inventario")}>Ver todo</button>
        </div>
        {mats.length === 0
          ? <p style={{ color: "var(--text3)", fontSize: 13 }}>Sin materiales en stock</p>
          : <div className="grid-3">
            {mats.map(m => {
              const pct = totalStock > 0 ? (m.stock_kg / totalStock) * 100 : 0;
              return (
                <div className="inv-item" key={m.id}>
                  <div className="inv-icon">{m.emoji}</div>
                  <div className="inv-info">
                    <div className="inv-name">{m.nombre}</div>
                    <div className="inv-meta">{m.codigo}</div>
                    <div className="progress-bar"><div className="progress-fill fill-green" style={{ width: `${pct}%` }} /></div>
                  </div>
                  <div className="inv-kg">{m.stock_kg.toFixed(1)}<span style={{ fontSize: 11, fontWeight: 400, color: "var(--text3)" }}> kg</span></div>
                </div>
              );
            })}
          </div>}
      </div>
    </div>
  );
}