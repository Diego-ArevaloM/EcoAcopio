import { useState } from "react";
import { Api } from "../services/api";

export default function ReportesPage({ app, showToast }) {
  const isAdmin = app.role === "admin";
  const [mes, setMes] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];

  const generar = async () => {
    setLoading(true);
    try {
      const data = await Api.reporte(mes, year);
      setResult(data);
    } catch (e) { showToast("error", "❌ " + e.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">📋 Reportes y Trazabilidad</h1>
        <p className="page-sub">Reportes de cierre mensual y exportación para entidades ambientales — RN-13</p>
      </div>
      <div className="card-relative card mb-16">
        {!isAdmin && (
          <div className="locked-overlay">
            <div style={{ fontSize: 36 }}>🔒</div>
            <div className="locked-text">Solo el Administrador puede acceder a los reportes — RN-10</div>
          </div>
        )}
        <div className="card-title">Generar Reporte de Período</div>
        <div className="grid-3 mb-16">
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Mes</label>
            <select className="form-select" value={mes} onChange={e => setMes(Number(e.target.value))}>
              {meses.map((m, i) => <option key={i} value={i + 1}>{m}</option>)}
            </select>
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label">Año</label>
            <select className="form-select" value={year} onChange={e => setYear(Number(e.target.value))}>
              <option value={2024}>2024</option><option value={2025}>2025</option><option value={2026}>2026</option>
            </select>
          </div>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 8 }}>
            <button className="btn btn-primary" onClick={generar} disabled={loading || !isAdmin}>{loading ? "Generando..." : "📊 Generar"}</button>
            <a href={Api.exportarCSV(mes, year)} className="btn btn-secondary" style={{ textDecoration: "none" }}>⬇️ CSV</a>
          </div>
        </div>
        {result && (
          <div>
            <div className="sep" />
            {result.stats?.alterado && (
              <div className="alert alert-warning mb-16"><span className="alert-icon">⚠️</span>Este reporte contiene transacciones que fueron modificadas post-registro. Verificar auditoría.</div>
            )}
            <div className="grid-4 mb-16">
              <div className="stat-card"><div className="stat-label">TOTAL ENTRADAS</div><div className="stat-value text-green mono">{result.stats?.total_entradas_kg?.toFixed(2)} kg</div></div>
              <div className="stat-card"><div className="stat-label">TOTAL SALIDAS</div><div className="stat-value text-red mono">{result.stats?.total_salidas_kg?.toFixed(2)} kg</div></div>
              <div className="stat-card"><div className="stat-label">TRANSACCIONES</div><div className="stat-value mono">{result.stats?.total_transacciones}</div></div>
              <div className="stat-card"><div className="stat-label">BALANCE NETO</div><div className={`stat-value mono ${result.stats?.balance_kg >= 0 ? "text-green" : "text-red"}`}>{result.stats?.balance_kg?.toFixed(2)} kg</div></div>
            </div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Fecha</th><th>Material</th><th>Proveedor</th><th>Peso (kg)</th><th>Tipo</th></tr></thead>
                <tbody>
                  {(result.transacciones || []).length === 0
                    ? <tr><td colSpan={5} style={{ textAlign: "center", color: "var(--text3)", padding: 24 }}>Sin transacciones en este período</td></tr>
                    : (result.transacciones || []).map((t, i) => (
                      <tr key={i}>
                        <td className="mono">{new Date(t.registrado_en).toLocaleDateString("es-PE")}</td>
                        <td>{t.emoji || ""} {t.material}{t.modificado && <span className="badge badge-amber" style={{ marginLeft: 6 }}>⚠ Modificado</span>}</td>
                        <td>{t.proveedor}</td>
                        <td className={`mono ${t.tipo === "entrada" ? "text-green" : "text-red"}`}>{t.tipo === "entrada" ? "+" : "−"}{parseFloat(t.peso_kg).toFixed(2)}</td>
                        <td><span className={`badge badge-${t.tipo === "entrada" ? "green" : "red"}`}>{t.tipo === "entrada" ? "Entrada" : "Salida"}</span></td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
