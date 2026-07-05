import { useEffect, useState } from "react";
import api, { extractError } from "../api.js";

export default function Report() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [checked, setChecked] = useState({});

  useEffect(() => {
    api
      .get("/report")
      .then((res) => setData(res.data))
      .catch((err) => setError(extractError(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="loading-text">Compiling your report…</p>;

  if (error) {
    return (
      <div>
        <h1>Full Report</h1>
        <div className="alert alert-error">{error}</div>
      </div>
    );
  }

  return (
    <div>
      <h1>Monthly Report — {data.month}</h1>

      <div className="card-row">
        <div className="card">
          <div className="stat-label">Health score</div>
          <div className="figure-lg neutral-accent">{data.health_score.score}/100</div>
        </div>
        <div className="card">
          <div className="stat-label">Total income</div>
          <div className="figure-lg">₹{data.budget.total_income.toLocaleString()}</div>
        </div>
        <div className="card">
          <div className="stat-label">Emergency fund</div>
          <div className="figure-lg positive">{data.savings_progress.percent_complete}%</div>
        </div>
      </div>

      <div className="card section-gap">
        <h2>Key insights</h2>
        <ul className="insight-list">
          {data.insights.map((insight, i) => (
            <li key={i}>{insight}</li>
          ))}
        </ul>
      </div>

      <div className="card">
        <h2>Action items</h2>
        {data.action_items.map((action, i) => (
          <label className="action-item" key={i}>
            <input
              type="checkbox"
              checked={!!checked[i]}
              onChange={() => setChecked((prev) => ({ ...prev, [i]: !prev[i] }))}
            />
            <span style={{ textDecoration: checked[i] ? "line-through" : "none", color: checked[i] ? "var(--text-faint)" : "var(--text)" }}>
              {action}
            </span>
          </label>
        ))}
      </div>

      <div className="card">
        <h2>
          Debt plan <span className="badge">{data.debt_plan.strategy}</span>
        </h2>
        <p>{data.debt_plan.note}</p>
        {data.debt_plan.order.length > 0 ? (
          <table className="ledger">
            <thead>
              <tr>
                <th>Debt</th>
                <th>Balance</th>
                <th>Interest</th>
                <th>Min. payment</th>
              </tr>
            </thead>
            <tbody>
              {data.debt_plan.order.map((d, i) => (
                <tr key={i}>
                  <td>{d.name}</td>
                  <td className="num">₹{d.balance.toLocaleString()}</td>
                  <td className="num">{d.interest_rate}%</td>
                  <td className="num">₹{d.min_payment.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No debts on file.</p>
        )}
      </div>

      <div className="card">
        <h2>Full budget breakdown</h2>
        <table className="ledger">
          <thead>
            <tr>
              <th>Category</th>
              <th>Allocated</th>
              <th>Spent</th>
              <th>Remaining</th>
            </tr>
          </thead>
          <tbody>
            {data.budget.categories.map((c) => (
              <tr key={c.category}>
                <td style={{ textTransform: "capitalize" }}>{c.category.replace("_", " ")}</td>
                <td className="num">₹{c.allocated.toLocaleString()}</td>
                <td className="num">₹{c.spent.toLocaleString()}</td>
                <td className={"num " + (c.remaining >= 0 ? "positive" : "negative")}>
                  ₹{c.remaining.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
