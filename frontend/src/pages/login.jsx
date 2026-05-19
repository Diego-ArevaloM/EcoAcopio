import { useState } from "react";
import { Api } from "../services/api";

export default function LoginPage({ onLogin }) {
  const [email, setEmail] = useState("");
  const [pass, setPass] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const doLogin = async () => {
    if (!email || !pass) { setErr("Ingresa tu email y contraseña."); return; }
    setLoading(true); setErr("");
    try {
      const user = await Api.login(email, pass);
      onLogin(user);
    } catch (e) {
      setErr(e.message);
    } finally { setLoading(false); }
  };

  const fillDemo = (role) => {
    if (role === "admin") { setEmail("admin@ecoacopio.pe"); setPass("admin123"); }
    else { setEmail("operario@ecoacopio.pe"); setPass("operario123"); }
  };

  return (
    <div className="login-screen">
      <div className="login-card">
        <div className="login-logo">
          <div className="logo-icon">♻️</div>
          <div>
            <div className="login-title">EcoAcopio ERP</div>
            <div style={{ fontSize: 12, color: "var(--text3)" }}>Sistema de Gestión de Acopio</div>
          </div>
        </div>
        {err && <div className="alert alert-error" style={{ marginBottom: 16 }}><span className="alert-icon">⚠️</span>{err}</div>}
        <div className="form-group">
          <label className="form-label">Correo Electrónico</label>
          <input className="form-input" type="email" placeholder="usuario@ecoacopio.pe" value={email}
            onChange={e => setEmail(e.target.value)} onKeyDown={e => e.key === "Enter" && doLogin()} />
        </div>
        <div className="form-group">
          <label className="form-label">Contraseña</label>
          <input className="form-input" type="password" placeholder="••••••••" value={pass}
            onChange={e => setPass(e.target.value)} onKeyDown={e => e.key === "Enter" && doLogin()} />
        </div>
        <button className="btn btn-primary btn-full btn-lg" onClick={doLogin} disabled={loading}>
          {loading ? <><span className="spinner" /> Ingresando...</> : "🔓 Ingresar"}
        </button>
        <div className="login-demo-btns">
          <button className="btn btn-amber btn-sm" style={{ flex: 1 }} onClick={() => fillDemo("admin")}>👤 Demo Admin</button>
          <button className="btn btn-ghost btn-sm" style={{ flex: 1 }} onClick={() => fillDemo("operario")}>👤 Demo Operario</button>
        </div>
      </div>
    </div>
  );
}
