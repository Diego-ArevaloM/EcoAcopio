import { useState } from "react";
import { Api } from "../services/api";

export default function ScannerPage({ app, showToast }) {
  const [desc, setDesc] = useState("");
  const [img, setImg] = useState(null);
  const [imgB64, setImgB64] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleFile = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    setImg(URL.createObjectURL(f));
    const reader = new FileReader();
    reader.onload = (ev) => setImgB64(ev.target.result.split(",")[1]);
    reader.readAsDataURL(f);
  };

  const analizar = async () => {
    if (!desc && !imgB64) { showToast("error", "Describe el objeto o sube una imagen."); return; }
    setLoading(true); setResult(null);
    try {
      const data = await Api.analizarIA({ descripcion: desc, imagen_base64: imgB64 });
      setResult(data);
    } catch (e) { showToast("error", "❌ " + e.message); }
    finally { setLoading(false); }
  };

  const guia = app.materiales.filter(m => m.activo).slice(0, 8);

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">🤖 Escáner de Reciclabilidad IA</h1>
        <p className="page-sub">Identificación de materiales reciclables mediante inteligencia artificial</p>
      </div>
      <div className="grid-2">
        <div>
          <div className="card mb-16">
            <div className="card-title">Descripción del Objeto / Imagen</div>
            <div className="form-group">
              <label className="form-label">Describe el objeto o pega una imagen</label>
              <textarea className="form-textarea" id="ai-desc" placeholder="Ej: Botella de plástico transparente con etiqueta de papel..." style={{ minHeight: 100 }} value={desc} onChange={e => setDesc(e.target.value)} />
            </div>
            <div className="scanner-area" onClick={() => document.getElementById("scan-file").click()}>
              <span className="scanner-icon">📷</span>
              <p className="scanner-text">Toca para cargar foto del objeto<br /><small>o arrastra la imagen aquí</small></p>
              <input type="file" id="scan-file" accept="image/*" style={{ display: "none" }} onChange={handleFile} />
            </div>
            {img && <div style={{ marginTop: 12 }}><img src={img} alt="preview" style={{ maxWidth: "100%", borderRadius: "var(--r)", border: "1px solid var(--border2)" }} /></div>}
            <button className="btn btn-primary btn-full btn-lg mt-12" onClick={analizar} disabled={loading}>
              {loading ? <><span className="spinner" /> Analizando...</> : "🤖 Analizar con IA"}
            </button>
          </div>
        </div>
        <div>
          <div className="card mb-16">
            <div className="flex-row mb-12"><div className="ai-label">RESULTADO DEL ANÁLISIS</div></div>
            {!result && !loading && <p className="text-muted" style={{ fontSize: 13, textAlign: "center", padding: 20 }}>El análisis aparecerá aquí después de procesar el objeto.</p>}
            {loading && <div style={{ textAlign: "center", padding: 20 }}><span className="spinner" style={{ width: 28, height: 28, borderWidth: 3 }} /></div>}
            {result && (
              <div>
                <div style={{ fontSize: 32, marginBottom: 8 }}>{result.emoji || "♻️"}</div>
                <div style={{ fontWeight: 700, fontSize: 18, color: "var(--text1)", marginBottom: 4 }}>{result.material || "—"}</div>
                <div style={{ fontSize: 13, color: "var(--text2)", marginBottom: 12 }}>{result.descripcion}</div>
                {result.reciclable !== undefined && (
                  <div className={`badge ${result.reciclable ? "badge-green" : "badge-red"}`} style={{ marginBottom: 8 }}>
                    {result.reciclable ? "✅ Reciclable" : "❌ No reciclable"}
                  </div>
                )}
                {result.confianza && <div style={{ fontSize: 12, color: "var(--text3)", marginTop: 4 }}>Confianza: {result.confianza}%</div>}
                {result.instrucciones && <div style={{ marginTop: 12, fontSize: 13, color: "var(--text2)", borderTop: "1px solid var(--border)", paddingTop: 12 }}>{result.instrucciones}</div>}
              </div>
            )}
          </div>
          <div className="card">
            <div className="card-title">Guía Rápida de Materiales</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {guia.map(m => (
                <div key={m.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderBottom: "1px solid var(--border)" }}>
                  <span style={{ fontSize: 20 }}>{m.emoji}</span>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text1)" }}>{m.nombre}</div>
                    <div style={{ fontSize: 11, color: "var(--text3)" }}>S/. {m.precio?.toFixed(2)}/kg · {m.categoria}</div>
                  </div>
                  <span className="badge badge-green" style={{ marginLeft: "auto" }}>Aceptado</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}