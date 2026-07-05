import { useState } from "react";
import api, { extractError } from "../api.js";

const emptyDebt = () => ({ name: "", balance: "", interest_rate: "", min_payment: "" });

export default function ProfileSetup() {
  const [income, setIncome] = useState("");
  const [risk, setRisk] = useState("moderate");
  const [savingsGoal, setSavingsGoal] = useState("");
  const [efTarget, setEfTarget] = useState("");
  const [efCurrent, setEfCurrent] = useState("");
  const [debts, setDebts] = useState([]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [busy, setBusy] = useState(false);

  function updateDebt(i, field, value) {
    setDebts((prev) => prev.map((d, idx) => (idx === i ? { ...d, [field]: value } : d)));
  }

  function addDebt() {
    setDebts((prev) => [...prev, emptyDebt()]);
  }

  function removeDebt(i) {
    setDebts((prev) => prev.filter((_, idx) => idx !== i));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!income || Number(income) <= 0) {
      setError("Enter your actual monthly income to continue — it drives every budget calculation below.");
      return;
    }

    setBusy(true);

    const payload = {
      monthly_income: Number(income),
      risk_tolerance: risk,
      savings_goal: savingsGoal ? Number(savingsGoal) : 0,
      emergency_fund_target: efTarget ? Number(efTarget) : 0,
      emergency_fund_current: efCurrent ? Number(efCurrent) : 0,
      debts: debts
        .filter((d) => d.name.trim())
        .map((d) => ({
          name: d.name,
          balance: Number(d.balance) || 0,
          interest_rate: Number(d.interest_rate) || 0,
          min_payment: Number(d.min_payment) || 0,
        })),
    };

    try {
      await api.post("/profile", payload);
      setSuccess(
        `Profile saved. Your wallet balance is now ₹${Number(income).toLocaleString()} for this month, ` +
          "and a starter budget has been generated — check the Budget tab."
      );
    } catch (err) {
      setError(extractError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h1>Profile Setup</h1>
      <p>
        Enter your real numbers below — your income sets this month's wallet balance, and everything
        else (budget, health score, suggestions) is calculated from what you enter here.
      </p>

      {error && <div className="alert alert-error">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      <form onSubmit={handleSubmit}>
        <div className="card">
          <h2>Income &amp; goals</h2>
          <div className="form-grid">
            <div className="field">
              <label>Monthly income (₹) *</label>
              <input
                type="number"
                value={income}
                onChange={(e) => setIncome(e.target.value)}
                min="0"
                placeholder="e.g. 45000"
                required
              />
            </div>
            <div className="field">
              <label>Risk tolerance</label>
              <select value={risk} onChange={(e) => setRisk(e.target.value)}>
                <option value="low">Low</option>
                <option value="moderate">Moderate</option>
                <option value="high">High</option>
              </select>
            </div>
            <div className="field">
              <label>Monthly savings goal (₹)</label>
              <input
                type="number"
                value={savingsGoal}
                onChange={(e) => setSavingsGoal(e.target.value)}
                min="0"
                placeholder="Optional — defaults to 10% of income"
              />
            </div>
            <div className="field">
              <label>Emergency fund target (₹)</label>
              <input
                type="number"
                value={efTarget}
                onChange={(e) => setEfTarget(e.target.value)}
                min="0"
                placeholder="e.g. 3x monthly income"
              />
            </div>
            <div className="field">
              <label>Emergency fund — saved so far (₹)</label>
              <input
                type="number"
                value={efCurrent}
                onChange={(e) => setEfCurrent(e.target.value)}
                min="0"
                placeholder="e.g. 0"
              />
            </div>
          </div>
        </div>

        <div className="card">
          <h2>Debts</h2>
          {debts.length === 0 && <p style={{ marginTop: 0 }}>No debts added. Add one below if applicable.</p>}
          {debts.map((debt, i) => (
            <div className="form-grid" key={i} style={{ marginBottom: 8 }}>
              <div className="field">
                <label>Name</label>
                <input
                  type="text"
                  value={debt.name}
                  onChange={(e) => updateDebt(i, "name", e.target.value)}
                  placeholder="e.g. Education Loan"
                />
              </div>
              <div className="field">
                <label>Balance (₹)</label>
                <input
                  type="number"
                  value={debt.balance}
                  onChange={(e) => updateDebt(i, "balance", e.target.value)}
                  min="0"
                />
              </div>
              <div className="field">
                <label>Interest rate (%)</label>
                <input
                  type="number"
                  value={debt.interest_rate}
                  onChange={(e) => updateDebt(i, "interest_rate", e.target.value)}
                  min="0"
                  step="0.1"
                />
              </div>
              <div className="field">
                <label>Min. monthly payment (₹)</label>
                <input
                  type="number"
                  value={debt.min_payment}
                  onChange={(e) => updateDebt(i, "min_payment", e.target.value)}
                  min="0"
                />
              </div>
              <button type="button" className="btn btn-ghost" onClick={() => removeDebt(i)}>
                Remove this debt
              </button>
            </div>
          ))}
          <button type="button" className="btn btn-ghost" onClick={addDebt}>
            + Add a debt
          </button>
        </div>

        <button className="btn btn-primary" type="submit" disabled={busy}>
          {busy ? "Saving…" : "Save profile"}
        </button>
      </form>
    </div>
  );
}

