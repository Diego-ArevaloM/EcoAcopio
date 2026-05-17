import { useState } from "react";
import { Api } from "../services/api";
import Modal from "../components/modal";

export default function ProveedoresPage({ app, onRefresh, showToast }) {
  const [modal, setModal] = useState(null); // null | "add" | "edit"
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ nombre: "", tipo_documento: "DNI", numero_documento: "", telefono: "" });
  const [loading, setLoading] = useState(false);

  const openAdd = () => { setForm({ nombre: "", tipo_documento: "DNI", numero_documento: "", telefono: "" }); setEditing(null); setModal("form"); };
  const openEdit = (p) => { setEditing(p); setForm({ nombre: p.nombre, tipo_documento: p.tipoDoc, numero_documento: p.documento, telefono: p.telefono }); setModal("form"); };

  const guardar = async () => {
    if (!form.nombre) { showToast("error", "El nombre es obligatorio."); return; }
    setLoading(true);
    try {
      if (editing) { await Api.actualizarProveedor(editing.id, form); showToast("success", "Proveedor actualizado."); }
      else { await Api.crearProveedor(form); showToast("success", "✅ Proveedor creado."); }
      setModal(null); onRefresh();
    } catch (e) { showToast("error", "❌ " + e.message); }
    finally { setLoading(false); }
  };

  return (
    <div className="page">
      <div className="page-header flex-between">
        <div>
          <h1 className="page-title">👥 Proveedores</h1>
          <p className="page-sub">Gestión de recicladores y recolectores — RN-08, RN-09</p>
        </div>
        <button className="btn btn-primary" onClick={openAdd}>+ Nuevo Proveedor</button>
      </div>
      <div className="alert alert-amber mb-16">
        <span className="alert-icon">🔒</span>
        <span><strong>RN-09:</strong> El proveedor "Reciclador Anónimo" es inmodificable y siempre está disponible.</span>
      </div>
      <div className="card">
        <div className="table-wrap">
          <table>
            <thead><tr><th>Nombre</th><th>Documento</th><th>Tipo Doc.</th><th>Teléfono</th><th>Transacciones</th><th>Estado</th><th>Acciones</th></tr></thead>
            <tbody>
              {app.proveedores.length === 0
                ? <tr><td colSpan={7} style={{ textAlign: "center", color: "var(--text3)", padding: 24 }}>Sin proveedores</td></tr>
                : app.proveedores.map(p => (
                  <tr key={p.id}>
                    <td><span className="main-cell">{p.nombre}{p.anonimo && <span className="badge badge-gray" style={{ marginLeft: 6 }}>Anónimo</span>}</span></td>
                    <td className="mono">{p.documento}</td>
                    <td>{p.tipoDoc}</td>
                    <td>{p.telefono}</td>
                    <td className="mono">{p.total_transacciones}</td>
                    <td><span className="badge badge-green">Activo</span></td>
                    <td>
                      <div className="table-actions">
                        {!p.anonimo && <button className="btn btn-ghost btn-sm" onClick={() => openEdit(p)}>✏️ Editar</button>}
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
          <div className="modal-title">{editing ? "✏️ Editar Proveedor" : "➕ Nuevo Proveedor"}</div>
          <div className="modal-sub">RN-08: El nombre es obligatorio.</div>
          <div className="form-group">
            <label className="form-label">Nombre completo <span className="req">*</span></label>
            <input className="form-input" value={form.nombre} onChange={e => setForm(f => ({ ...f, nombre: e.target.value }))} placeholder="Nombre del reciclador..." />
          </div>
          <div className="form-group">
            <label className="form-label">Tipo de Documento</label>
            <select className="form-select" value={form.tipo_documento} onChange={e => setForm(f => ({ ...f, tipo_documento: e.target.value }))}>
              <option>DNI</option><option>RUC</option><option>CE</option><option>Pasaporte</option>
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Número de Documento</label>
            <input className="form-input" value={form.numero_documento} onChange={e => setForm(f => ({ ...f, numero_documento: e.target.value }))} placeholder="12345678" />
          </div>
          <div className="form-group">
            <label className="form-label">Teléfono</label>
            <input className="form-input" value={form.telefono} onChange={e => setForm(f => ({ ...f, telefono: e.target.value }))} placeholder="987654321" />
          </div>
          <div className="modal-actions">
            <button className="btn btn-ghost" onClick={() => setModal(null)}>Cancelar</button>
            <button className="btn btn-primary" onClick={guardar} disabled={loading}>{loading ? "Guardando..." : "Guardar"}</button>
          </div>
        </Modal>
      )}
    </div>
  );
}