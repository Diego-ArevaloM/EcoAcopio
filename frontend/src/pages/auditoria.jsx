import { useState, useEffect } from "react";
import { Api } from "../services/api";

export default function AuditoriaPage({ app, showToast }) {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    Api.auditoria(100).then(setData).catch(e => showToast("error", "Error cargando auditoría: " + e.message));
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">🔍 Log de Auditoría</h1>
        <p className="page-sub">Registro inmutable de todas las modificaciones — RN-12</p>
      </div>
      <div className="grid-21">
        <div className="card">
          <div className="card-title">Historial de Cambios</div>
          {!data
            ? <div style={{ textAlign: "center", padding: 24 }}><span className="spinner" style={{ width: 24, height: 24 }} /></div>
            : <div>
              {(data.items || []).map((l, i) => (
                <div className="audit-item" key={i}>
                  <div className="audit-dot" style={{ background: "var(--amber)" }} />
                  <div className="audit-content">
                    <div className="audit-title"><strong>{l.accion}</strong> — {l.tabla_afectada || "—"}</div>
                    <div className="audit-meta">{l.descripcion || "—"}</div>
                    <div className="audit-meta">👤 {l.usuario_email} · {new Date(l.created_at).toLocaleString("es-PE", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}</div>
                  </div>
                </div>
              ))}
            </div>}
        </div>
        <div className="card">
          <div className="card-title">Resumen de Actividad</div>
          {data && (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              <div className="stat-card"><div className="stat-label">TOTAL CAMBIOS</div><div className="stat-value text-amber">{data.total}</div></div>
              <div className="stat-card"><div className="stat-label">HOY</div><div className="stat-value">{data.hoy}</div></div>
              <div style={{ background: "var(--amber-bg)", border: "1px solid var(--amber-border)", borderRadius: "var(--r)", padding: 12 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: "var(--amber)", marginBottom: 4 }}>RN-12 ACTIVO</div>
                <div style={{ fontSize: 12, color: "var(--text2)" }}>Todo cambio realizado queda registrado en este log inmutable.</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
