import { useEffect, useState } from "react";
import api, { extractError } from "../api.js";

export default function ExpenseHistory() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [monthFilter, setMonthFilter] = useState("");

  function load(month) {
    setLoading(true);
    setError("");
    const query = month ? `?month=${month}` : "";
    api
      .get(`/expense/history${query}`)
      .then((res) => setData(res.data))
      .catch((err) => setError(extractError(err)))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleFilter(e) {
    e.preventDefault();
    load(monthFilter || undefined);
  }

  if (loading) return <p className="loading-text">Loading your expense history…</p>;

  if (error) {
    return (
      <div>
        <h1>Expense History</h1>
        <div className="alert alert-error">{error}</div>
      </div>
    );
  }

  return (
    <div>
      <h1>Expense History</h1>
      <p>Every expense you've logged, most recent first.</p>

      <div className="card-row">
        <div className="card">
          <div className="stat-label">
            {data.month === "all" ? "Total spent (all time)" : `Total spent — ${data.month}`}
          </div>
          <div className="figure-lg neutral-accent">₹{data.total_spent.toLocaleString()}</div>
        </div>
        <div className="card">
          <div className="stat-label">Current overall balance</div>
          <div className={"figure-lg " + (data.current_balance >= 0 ? "positive" : "negative")}>
            ₹{data.current_balance.toLocaleString()}
          </div>
        </div>
      </div>

      <div className="card">
        <form onSubmit={handleFilter} style={{ display: "flex", gap: 12, alignItems: "flex-end" }}>
          <div className="field" style={{ marginBottom: 0, flex: 1 }}>
            <label>Filter by month</label>
            <input
              type="month"
              value={monthFilter}
              onChange={(e) => setMonthFilter(e.target.value)}
              placeholder="YYYY-MM"
            />
          </div>
          <button className="btn btn-ghost" type="submit">
            Apply filter
          </button>
          {monthFilter && (
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                setMonthFilter("");
                load();
              }}
            >
              Clear
            </button>
          )}
        </form>
      </div>

      <div className="card">
        {data.transactions.length === 0 ? (
          <div className="empty-state">
            <h3>No expenses logged yet</h3>
            <p>Once you log an expense, it'll show up here with a running history.</p>
          </div>
        ) : (
          <table className="ledger">
            <thead>
              <tr>
                <th>Date</th>
                <th>Description</th>
                <th>Category</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              {data.transactions.map((t) => (
                <tr key={t.id}>
                  <td className="figure">{new Date(t.created_at).toLocaleDateString()}</td>
                  <td>{t.description}</td>
                  <td style={{ textTransform: "capitalize" }}>{t.category.replace("_", " ")}</td>
                  <td className="num negative">₹{t.amount.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
