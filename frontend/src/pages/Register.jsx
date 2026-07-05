import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [userId, setUserId] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    const result = await register(userId, email, password);
    setBusy(false);
    if (result.ok) {
      navigate("/profile");
    } else {
      setError(result.error);
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <div className="auth-mark">
          <span className="brand-mark">$</span> SmartBudget AI
        </div>
        <p className="auth-sub">Open a new ledger.</p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="userId">User ID</label>
            <input
              id="userId"
              type="text"
              placeholder="e.g. sri001"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={8}
              required
            />
          </div>
          <button className="btn btn-primary btn-block" type="submit" disabled={busy}>
            {busy ? "Creating account…" : "Create account"}
          </button>
        </form>

        <div className="auth-switch">
          Already have one? <button onClick={() => navigate("/login")}>Sign in</button>
        </div>
      </div>
    </div>
  );
}
