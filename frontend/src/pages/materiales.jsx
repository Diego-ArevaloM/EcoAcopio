import { useState } from "react";
import { Api } from "../services/api";
import Modal from "../components/Modal";

export default function MaterialesPage({ app, onRefresh, showToast }) {
  const [modal, setModal] = useState(null);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ codigo: "", nombre: "", emoji: "♻️", precio_referencial: "" });
  const [loading, setLoading] = useState(false);

  const openAdd = () => { setForm({ codigo: "", nombre: "", emoji: "♻️", precio_referencial: "" }); setEditing(null); setModal("form"); };
  const openEdit = (m) => { setEditing(m); setForm({ codigo: m.codigo, nombre: m.nombre, emoji: m.emoji, precio_referencial: m.precio }); setModal("edit"); };

  const crear = async () => {
    if (!form.codigo || !form.nombre) { showToast("error", "Código y nombre son obligatorios."); return; }
    setLoading(true);
    try {
      await Api.crearMaterial({ ...form, precio_referencial: parseFloat(form.precio_referencial) || 0 });
      showToast("success", "✅ Material creado.");
      setModal(null); onRefresh();
    } catch (e) { showToast("error", "❌ " + e.message); }
    finally { setLoading(false); }
  };

  const editar = async () => {
    setLoading(true);
    try {
      await Api.actualizarMaterial(editing.id, { precio_referencial: parseFloat(form.precio_referencial), emoji: form.emoji });
      showToast("success", "Material actualizado.");
      setModal(null); onRefresh();
    } catch (e) { showToast("error", "❌ " + e.message); }
    finally { setLoading(false); }
  };

  const toggle = async (id) => {
    try {
      await Api.toggleMaterial(id);
      onRefresh();
      showToast("success", "Estado actualizado.");
    } catch (e) { showToast("error", "❌ " + e.message); }
  };

  return (
    <div className="page">
      <div className="page-header flex-between">
        <div>
          <h1 className="page-title">🏷️ Lista Maestra de Materiales</h1>
          <p className="page-sub">Solo el Administrador puede crear, editar o desactivar materiales — RN-07</p>
        </div>
        <button className="btn btn-primary" onClick={openAdd}>+ Nuevo Material</button>
      </div>
      <div className="card">
        <div className="table-wrap">
          <table>
            <thead><tr><th>Código</th><th>Material</th><th>Categoría</th><th>Precio Ref. (S/./kg)</th><th>Stock Actual</th><th>Estado</th><th>Acciones</th></tr></thead>
            <tbody>
              {app.materiales.length === 0
                ? <tr><td colSpan={7} style={{ textAlign: "center", color: "var(--text3)", padding: 24 }}>Sin materiales</td></tr>
                : app.materiales.map(m => (
                  <tr key={m.id}>
                    <td className="mono" style={{ fontSize: 12 }}>{m.codigo}</td>
                    <td><span className="main-cell">{m.emoji} {m.nombre}</span></td>
                    <td>{m.categoria}</td>
                    <td className="mono">S/. {m.precio?.toFixed(2)}</td>
                    <td className="mono text-green">{(m.stock_kg || 0).toFixed(2)} kg</td>
                    <td><span className={`badge ${m.activo ? "badge-green" : "badge-gray"}`}>{m.activo ? "Activo" : "Inactivo"}</span></td>
                    <td>
                      <div className="table-actions">
                        <button className="btn btn-ghost btn-sm" onClick={() => openEdit(m)}>✏️</button>
                        <button className={`btn btn-sm ${m.activo ? "btn-danger" : "btn-amber"}`} onClick={() => toggle(m.id)}>{m.activo ? "Desactivar" : "Activar"}</button>
                      </div>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>

      {modal === "form" && (
        <Modal onClose={() => setModal(null)}>
          <div className="modal-title">➕ Nuevo Material</div>
          <div className="form-group">
            <label className="form-label">Código <span className="req">*</span></label>
            <input className="form-input" value={form.codigo} onChange={e => setForm(f => ({ ...f, codigo: e.target.value }))} placeholder="PET-01" />
          </div>
          <div className="form-group">
            <label className="form-label">Nombre <span className="req">*</span></label>
            <input className="form-input" value={form.nombre} onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))} placeholder="Plástico PET" />
          </div>
          <div className="form-group">
            <label className="form-label">Emoji</label>
            <input className="form-input" value={form.emoji} onChange={e => setForm(f => ({ ...f, emoji: e.target.value }))} maxLength={4} />
          </div>
          <div className="form-group">
            <label className="form-label">Precio ref. (S/./kg)</label>
            <input type="number" className="form-input" value={form.precio_referencial} onChange={e => setForm(f => ({ ...f, precio_referencial: e.target.value }))} step="0.01" min="0" />
          </div>
          <div className="modal-actions">
            <button className="btn btn-ghost" onClick={() => setModal(null)}>Cancelar</button>
            <button className="btn btn-primary" onClick={crear} disabled={loading}>{loading ? "Creando..." : "Crear Material"}</button>
          </div>
        </Modal>
      )}

      {modal === "edit" && (
        <Modal onClose={() => setModal(null)}>
          <div className="modal-title">✏️ Editar Material: {editing?.nombre}</div>
          <div className="form-group">
            <label className="form-label">Precio ref. (S/./kg)</label>
            <input type="number" className="form-input" value={form.precio_referencial} onChange={e => setForm(f => ({ ...f, precio_referencial: e.target.value }))} step="0.01" min="0" />
          </div>
          <div className="form-group">
            <label className="form-label">Emoji</label>
            <input className="form-input" value={form.emoji} onChange={e => setForm(f => ({ ...f, emoji: e.target.value }))} maxLength={4} />
          </div>
          <div className="modal-actions">
            <button className="btn btn-ghost" onClick={() => setModal(null)}>Cancelar</button>
            <button className="btn btn-amber" onClick={editar} disabled={loading}>{loading ? "Guardando..." : "Guardar Cambios"}</button>
          </div>
        </Modal>
      )}
    </div>
  );
}
