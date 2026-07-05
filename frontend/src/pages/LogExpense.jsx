import { useState } from "react";
import { Link } from "react-router-dom";
import api, { extractError } from "../api.js";

export default function LogExpense() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setResult(null);
    setBusy(true);
    try {
      const res = await api.post("/expense", { text });
      setResult(res.data);
      setText("");
    } catch (err) {
      setError(extractError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h1>Log an Expense</h1>
      <p>
        Describe what you spent in plain language — it's categorized automatically and deducted from
        both your overall balance and that category's budget. See{" "}
        <Link to="/expense-history">Expense History</Link> for the full log.
      </p>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Expense description</label>
            <input
              type="text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="e.g. spent 500 on groceries today"
              autoFocus
            />
          </div>
          <button className="btn btn-primary" type="submit" disabled={busy || !text.trim()}>
            {busy ? "Logging…" : "Log expense"}
          </button>
        </form>
      </div>

      {result && (
        <div className="card section-gap">
          <div className="stat-label">Logged</div>
          <p style={{ color: "var(--text)", marginBottom: 16 }}>{result.message}</p>
          <div className="card-row">
            <div className="card">
              <div className="stat-label">Category</div>
              <div className="figure-lg neutral-accent">{result.category}</div>
            </div>
            <div className="card">
              <div className="stat-label">Amount</div>
              <div className="figure-lg">₹{Number(result.amount).toLocaleString()}</div>
            </div>
            {result.remaining_in_category !== null && (
              <div className="card">
                <div className="stat-label">Remaining in category</div>
                <div className={"figure-lg " + (result.remaining_in_category >= 0 ? "positive" : "negative")}>
                  ₹{Number(result.remaining_in_category).toLocaleString()}
                </div>
              </div>
            )}
            <div className="card">
              <div className="stat-label">Overall balance left</div>
              <div className={"figure-lg " + (result.current_balance >= 0 ? "positive" : "negative")}>
                ₹{Number(result.current_balance).toLocaleString()}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

