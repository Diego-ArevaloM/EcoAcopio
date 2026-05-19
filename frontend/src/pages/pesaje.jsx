import { useState, useEffect } from "react";
import { Api } from "../services/api";

export default function PesajePage({ app, onRefresh, showToast }) {
  const [material, setMaterial] = useState("");
  const [proveedor, setProveedor] = useState("");
  const [peso, setPeso] = useState("");
  const [obs, setObs] = useState("");
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [hist, setHist] = useState([]);
  const [clock, setClock] = useState("");

  const [salidaMat, setSalidaMat] = useState("");
  const [salidaPeso, setSalidaPeso] = useState("");
  const [salidaDest, setSalidaDest] = useState("");

  useEffect(() => {
    const tick = () => setClock(new Date().toLocaleString("es-PE", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit" }));
    tick();
    const iv = setInterval(tick, 1000);
    Api.pesajes("?limit=5").then(d => setHist(d.items || [])).catch(() => {});
    return () => clearInterval(iv);
  }, []);

  const validate = () => {
    const e = {};
    if (!material) e.material = "Debe seleccionar un material.";
    if (!proveedor) e.proveedor = "Debe seleccionar un proveedor.";
    if (!peso || parseFloat(peso) <= 0) e.peso = "El peso debe ser mayor a cero — RN-01.";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const registrar = async () => {
    if (!validate()) return;
    const kg = parseFloat(peso);
    if (kg > 5000) {
      const ok = window.confirm(`⚠️ RN-04: El peso ${kg} kg es inusualmente alto (> 5,000 kg). ¿Desea continuar?`);
      if (!ok) return;
    }
    setLoading(true);
    try {
      await Api.registrarPesaje({ material_id: material, proveedor_id: proveedor, peso_kg: kg, observaciones: obs, tipo: "entrada" });
      showToast("success", "✅ Pesaje registrado correctamente.");
      setMaterial(""); setProveedor(""); setPeso(""); setObs("");
      const [d] = await Promise.all([Api.pesajes("?limit=5")]);
      setHist(d.items || []);
      onRefresh();
    } catch (e) { showToast("error", "❌ " + e.message); }
    finally { setLoading(false); }
  };

  const registrarSalida = async () => {
    if (!salidaMat || !salidaPeso || parseFloat(salidaPeso) <= 0) {
      showToast("error", "Complete todos los campos de salida.");
      return;
    }
    const matObj = app.materiales.find(m => m.id === salidaMat);
    const kg = parseFloat(salidaPeso);
    if (matObj && kg > (matObj.stock_kg || 0)) {
      showToast("error", `❌ RN-06: Stock insuficiente. Disponible: ${matObj.stock_kg?.toFixed(2)} kg.`);
      return;
    }
    setLoading(true);
    try {
      await Api.registrarPesaje({ material_id: salidaMat, proveedor_id: app.proveedores[0]?.id, peso_kg: kg, observaciones: salidaDest, tipo: "salida" });
      showToast("success", "📤 Salida registrada.");
      setSalidaMat(""); setSalidaPeso(""); setSalidaDest("");
      onRefresh();
    } catch (e) { showToast("error", "❌ " + e.message); }
    finally { setLoading(false); }
  };

  const matActual = app.materiales.find(m => m.id === material);

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">⚖️ Registro de Pesaje</h1>
        <p className="page-sub">Ingreso de material al centro de acopio</p>
      </div>
      <div className="grid-12">
        <div className="card">
          <div className="card-title">Nueva Transacción de Entrada</div>
          <div className="alert alert-info" style={{ marginBottom: 16 }}>
            <span className="alert-icon">🕐</span>
            <div><strong>RN-03:</strong> La fecha y hora son registradas automáticamente por el servidor. No modificables.</div>
          </div>
          <div className="form-group">
            <label className="form-label">Fecha y Hora (automática) <span className="req">*</span></label>
            <div className="field-readonly">{clock}</div>
            <div className="form-hint">Generado por el servidor — RN-03</div>
          </div>
          <div className="form-group">
            <label className="form-label">Material <span className="req">*</span></label>
            <select className={`form-select${errors.material ? " error" : ""}`} value={material} onChange={e => setMaterial(e.target.value)}>
              <option value="">— Seleccionar material —</option>
              {app.materiales.filter(m => m.activo).map(m => <option key={m.id} value={m.id}>{m.emoji} {m.nombre}</option>)}
            </select>
            {errors.material && <div className="form-error">⚠ {errors.material}</div>}
            <div className="form-hint">RN-07: Solo materiales de la lista maestra.</div>
          </div>
          <div className="form-group">
            <label className="form-label">Proveedor / Reciclador <span className="req">*</span></label>
            <select className={`form-select${errors.proveedor ? " error" : ""}`} value={proveedor} onChange={e => setProveedor(e.target.value)}>
              <option value="">— Seleccionar proveedor —</option>
              {app.proveedores.map(p => <option key={p.id} value={p.id}>{p.nombre}</option>)}
            </select>
            {errors.proveedor && <div className="form-error">⚠ {errors.proveedor}</div>}
          </div>
          <div className="form-group">
            <label className="form-label">Peso Registrado (kg) <span className="req">*</span></label>
            <input type="number" className={`form-input${errors.peso ? " error" : ""}`} placeholder="0.00" step="0.01" min="0.01"
              value={peso} onChange={e => setPeso(e.target.value)} />
            {errors.peso && <div className="form-error">⚠ {errors.peso}</div>}
            <div className="form-hint">RN-01: Solo valores positivos. RN-04: Alerta si &gt; 5,000 kg.</div>
          </div>
          <div className="form-group">
            <label className="form-label">Observaciones (opcional)</label>
            <textarea className="form-textarea" placeholder="Estado del material, condiciones especiales..." value={obs} onChange={e => setObs(e.target.value)} />
          </div>
          <button className="btn btn-primary btn-full btn-lg" onClick={registrar} disabled={loading}>
            {loading ? <><span className="spinner" /> Registrando...</> : "✅ Registrar Pesaje"}
          </button>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div className="card">
            <div className="card-title">Vista Previa del Stock Afectado</div>
            {matActual
              ? <div>
                <div style={{ fontSize: 28, marginBottom: 8 }}>{matActual.emoji}</div>
                <div style={{ fontWeight: 600, color: "var(--text1)" }}>{matActual.nombre}</div>
                <div style={{ fontSize: 12, color: "var(--text3)", marginTop: 4 }}>Stock actual</div>
                <div style={{ fontFamily: "var(--mono)", fontSize: 24, color: "var(--green)", fontWeight: 700 }}>{(matActual.stock_kg || 0).toFixed(2)} kg</div>
                {peso && <div style={{ fontSize: 12, color: "var(--blue)", marginTop: 4 }}>+ {parseFloat(peso || 0).toFixed(2)} kg → {((matActual.stock_kg || 0) + parseFloat(peso || 0)).toFixed(2)} kg</div>}
              </div>
              : <p className="text-muted" style={{ fontSize: 13 }}>Seleccione un material para ver el stock actual.</p>}
          </div>
          <div className="card">
            <div className="card-title">Últimas 5 Transacciones</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {hist.length === 0
                ? <p className="text-muted" style={{ fontSize: 13 }}>Sin registros.</p>
                : hist.map(t => (
                  <div className="hist-item" key={t.id}>
                    <div className="hist-item-left">
                      <div className="hist-item-mat">{t.emoji || "♻️"} {t.material}</div>
                      <div className="hist-item-meta">{t.proveedor}</div>
                    </div>
                    <div className="hist-item-kg" style={{ color: t.tipo === "entrada" ? "var(--green)" : "var(--red)" }}>
                      {t.tipo === "entrada" ? "+" : "−"}{parseFloat(t.peso_kg).toFixed(2)} kg
                    </div>
                  </div>
                ))}
            </div>
          </div>
          <div className="card">
            <div className="card-title">🔴 Registro de Salida de Material</div>
            <div className="form-group">
              <label className="form-label">Material a retirar</label>
              <select className="form-select" value={salidaMat} onChange={e => setSalidaMat(e.target.value)}>
                <option value="">— Seleccionar —</option>
                {app.materiales.filter(m => m.activo && m.stock_kg > 0).map(m => <option key={m.id} value={m.id}>{m.emoji} {m.nombre} ({m.stock_kg?.toFixed(1)} kg)</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Cantidad (kg)</label>
              <input type="number" className="form-input" placeholder="0.00" step="0.01" min="0.01" value={salidaPeso} onChange={e => setSalidaPeso(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Destino / Cliente</label>
              <input type="text" className="form-input" placeholder="Empresa compradora..." value={salidaDest} onChange={e => setSalidaDest(e.target.value)} />
            </div>
            <button className="btn btn-danger btn-full" onClick={registrarSalida} disabled={loading}>📤 Registrar Salida</button>
            <div className="form-hint mt-8">RN-06: Se bloqueará si el peso supera el stock disponible.</div>
          </div>
        </div>
      </div>
    </div>
  );
}
