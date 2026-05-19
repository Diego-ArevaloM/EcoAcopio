import { useState } from "react";

export default function InventarioPage({ app }) {
  const [search, setSearch] = useState("");
  const items = app.materiales.filter(m => m.nombre.toLowerCase().includes(search.toLowerCase()) || m.codigo.toLowerCase().includes(search.toLowerCase()));
  const totalKg = items.reduce((s, m) => s + (m.stock_kg || 0), 0);
  const cats = new Set(items.filter(m => m.stock_kg > 0).map(m => m.categoria)).size;
  const mayor = items.reduce((a, b) => (b.stock_kg || 0) > (a.stock_kg || 0) ? b : a, items[0]);

  const getLevel = (kg) => {
    if (kg > 500) return { label: "Alto", cls: "fill-green", badge: "badge-green" };
    if (kg > 100) return { label: "Medio", cls: "fill-amber", badge: "badge-amber" };
    return { label: "Bajo", cls: "fill-red", badge: "badge-red" };
  };

  return (
    <div className="page">
      <div className="page-header flex-between">
        <div>
          <h1 className="page-title">📦 Inventario General</h1>
          <p className="page-sub">Stock acumulado actualizado en tiempo real — RN-05</p>
        </div>
        <div className="search-wrap">
          <span className="search-icon">🔍</span>
          <input type="text" className="form-input" placeholder="Buscar material..." value={search} onChange={e => setSearch(e.target.value)} style={{ width: 200 }} />
        </div>
      </div>
      <div className="grid-4 mb-16">
        <div className="stat-card"><div className="stat-label">TOTAL STOCK</div><div className="stat-value text-green mono">{totalKg.toFixed(2)} kg</div></div>
        <div className="stat-card"><div className="stat-label">CATEGORÍAS CON STOCK</div><div className="stat-value text-amber mono">{cats}</div></div>
        <div className="stat-card"><div className="stat-label">MAYOR VOLUMEN</div><div className="stat-value text-blue" style={{ fontSize: 16 }}>{mayor ? `${mayor.emoji} ${mayor.nombre}` : "—"}</div></div>
        <div className="stat-card"><div className="stat-label">ACTUALIZACIÓN</div><div className="stat-value" style={{ fontSize: 14, fontFamily: "var(--mono)" }}>{new Date().toLocaleTimeString("es-PE")}</div></div>
      </div>
      <div className="card">
        <div className="table-wrap">
          <table>
            <thead><tr><th>ID</th><th>Material</th><th>Categoría</th><th>Stock (kg)</th><th>Nivel</th><th>% del Total</th><th>Estado</th></tr></thead>
            <tbody>
              {items.length === 0
                ? <tr><td colSpan={7} style={{ textAlign: "center", color: "var(--text3)", padding: 24 }}>Sin resultados</td></tr>
                : items.map(m => {
                  const pct = totalKg > 0 ? ((m.stock_kg || 0) / totalKg * 100).toFixed(1) : "0.0";
                  const lvl = getLevel(m.stock_kg || 0);
                  return (
                    <tr key={m.id}>
                      <td className="mono" style={{ fontSize: 12, color: "var(--text3)" }}>{m.codigo}</td>
                      <td><span className="main-cell">{m.emoji} {m.nombre}</span></td>
                      <td>{m.categoria}</td>
                      <td className="mono text-green" style={{ fontWeight: 700 }}>{(m.stock_kg || 0).toFixed(2)}</td>
                      <td>
                        <div style={{ minWidth: 80 }}>
                          <div style={{ fontSize: 11, color: "var(--text3)" }}>{lvl.label}</div>
                          <div className="progress-bar"><div className={`progress-fill ${lvl.cls}`} style={{ width: `${Math.min(100, (m.stock_kg || 0) / 1000 * 100)}%` }} /></div>
                        </div>
                      </td>
                      <td className="mono" style={{ fontSize: 12 }}>{pct}%</td>
                      <td><span className={`badge ${m.activo ? "badge-green" : "badge-gray"}`}>{m.activo ? "Activo" : "Inactivo"}</span></td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
