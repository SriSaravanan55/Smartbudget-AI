import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import api, { extractError } from "../api.js";

const LEVEL_LABEL = {
  starter: "Starter suggestion",
  partially_personalized: "Partially personalized",
  personalized: "Fully personalized",
};

export default function Budget() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const [suggestion, setSuggestion] = useState(null);
  const [suggestionError, setSuggestionError] = useState("");
  const [suggestionLoading, setSuggestionLoading] = useState(false);
  const [showSuggestion, setShowSuggestion] = useState(false);
  const [applying, setApplying] = useState(false);
  const [applySuccess, setApplySuccess] = useState("");

  function loadBudget() {
    setLoading(true);
    api
      .get("/budget")
      .then((res) => setData(res.data))
      .catch((err) => setError(extractError(err)))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadBudget();
  }, []);

  function loadSuggestion() {
    setSuggestionLoading(true);
    setSuggestionError("");
    api
      .get("/budget/suggested")
      .then((res) => {
        setSuggestion(res.data);
        setShowSuggestion(true);
      })
      .catch((err) => setSuggestionError(extractError(err)))
      .finally(() => setSuggestionLoading(false));
  }

  async function handleApply() {
    setApplying(true);
    setApplySuccess("");
    try {
      const res = await api.post("/budget/apply-suggested");
      setData(res.data);
      setShowSuggestion(false);
      setApplySuccess("Suggested budget applied. Your allocations below now reflect it.");
    } catch (err) {
      setSuggestionError(extractError(err));
    } finally {
      setApplying(false);
    }
  }

  if (loading) return <p className="loading-text">Loading your budget…</p>;

  if (error) {
    return (
      <div>
        <h1>Budget</h1>
        <div className="alert alert-error">{error}</div>
        <p>Set up your profile first on the Profile Setup tab.</p>
      </div>
    );
  }

  const chartData = data.categories.map((c) => ({
    name: c.category.replace("_", " "),
    Allocated: c.allocated,
    Spent: c.spent,
  }));

  return (
    <div>
      <h1>Monthly Budget</h1>
      <p>{data.reasoning}</p>

      {applySuccess && <div className="alert alert-success">{applySuccess}</div>}

      <div className="card-row">
        <div className="card">
          <div className="stat-label">Total income — {data.month}</div>
          <div className="figure-lg neutral-accent">₹{data.total_income.toLocaleString()}</div>
        </div>
        <div className="card">
          <div className="stat-label">Overall balance left</div>
          <div className={"figure-lg " + (data.current_balance >= 0 ? "positive" : "negative")}>
            ₹{data.current_balance.toLocaleString()}
          </div>
        </div>
      </div>

      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <div>
            <h2 style={{ marginBottom: 4 }}>Suggested budget</h2>
            <p style={{ margin: 0 }}>
              A smarter allocation based on your income and, once you've logged expenses, your actual
              spending per category.
            </p>
          </div>
          <button className="btn btn-ghost" onClick={loadSuggestion} disabled={suggestionLoading}>
            {suggestionLoading ? "Thinking…" : showSuggestion ? "Refresh suggestion" : "View suggestion"}
          </button>
        </div>

        {suggestionError && (
          <div className="alert alert-error section-gap">{suggestionError}</div>
        )}

        {showSuggestion && suggestion && (
          <div className="section-gap">
            <span className="badge">{LEVEL_LABEL[suggestion.personalization_level]}</span>
            <p style={{ marginTop: 10 }}>{suggestion.reasoning}</p>

            <table className="ledger">
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Suggested</th>
                  <th>% of income</th>
                  <th>Based on</th>
                </tr>
              </thead>
              <tbody>
                {suggestion.categories.map((c) => (
                  <tr key={c.category}>
                    <td style={{ textTransform: "capitalize" }}>{c.category.replace("_", " ")}</td>
                    <td className="num">₹{c.suggested_allocated.toLocaleString()}</td>
                    <td className="num">{c.percent_of_income}%</td>
                    <td>
                      <span className="badge">{c.based_on}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <button className="btn btn-primary section-gap" onClick={handleApply} disabled={applying}>
              {applying ? "Applying…" : "Apply this budget"}
            </button>
          </div>
        )}
      </div>

      <div className="card">
        <h2>Allocated vs. spent</h2>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a4a43" />
            <XAxis dataKey="name" tick={{ fill: "#9fb3ac", fontSize: 11 }} interval={0} angle={-25} textAnchor="end" height={70} />
            <YAxis tick={{ fill: "#9fb3ac", fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: "#16302b", border: "1px solid #2a4a43", borderRadius: 6, color: "#f2efe6" }}
            />
            <Bar dataKey="Allocated" fill="#c9a227" radius={[3, 3, 0, 0]} />
            <Bar dataKey="Spent" fill="#7fb685" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <h2>Category breakdown</h2>
        <table className="ledger">
          <thead>
            <tr>
              <th>Category</th>
              <th>Allocated</th>
              <th>Spent</th>
              <th>Remaining</th>
              <th>% of income</th>
            </tr>
          </thead>
          <tbody>
            {data.categories.map((c) => (
              <tr key={c.category}>
                <td style={{ textTransform: "capitalize" }}>{c.category.replace("_", " ")}</td>
                <td className="num">₹{c.allocated.toLocaleString()}</td>
                <td className="num">₹{c.spent.toLocaleString()}</td>
                <td className={"num " + (c.remaining >= 0 ? "positive" : "negative")}>
                  ₹{c.remaining.toLocaleString()}
                </td>
                <td className="num">{c.percent_of_income}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

