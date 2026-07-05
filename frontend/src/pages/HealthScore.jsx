import { useEffect, useState } from "react";
import { RadialBarChart, RadialBar, PolarAngleAxis } from "recharts";
import api, { extractError } from "../api.js";

function scoreColor(score) {
  if (score >= 80) return "#7fb685";
  if (score >= 60) return "#c9a227";
  if (score >= 40) return "#e0c15c";
  return "#e2725b";
}

export default function HealthScore() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get("/health-score")
      .then((res) => setData(res.data))
      .catch((err) => setError(extractError(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="loading-text">Calculating your score…</p>;

  if (error) {
    return (
      <div>
        <h1>Financial Health Score</h1>
        <div className="alert alert-error">{error}</div>
      </div>
    );
  }

  const color = scoreColor(data.score);
  const chartData = [{ name: "score", value: data.score, fill: color }];

  return (
    <div>
      <h1>Financial Health Score</h1>

      <div className="card" style={{ display: "flex", alignItems: "center", gap: 32, flexWrap: "wrap" }}>
        <RadialBarChart
          width={200}
          height={200}
          cx={100}
          cy={100}
          innerRadius={70}
          outerRadius={95}
          barSize={16}
          data={chartData}
          startAngle={90}
          endAngle={-270}
        >
          <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
          <RadialBar background={{ fill: "#1c3a33" }} dataKey="value" cornerRadius={8} />
          <text
            x={100}
            y={95}
            textAnchor="middle"
            dominantBaseline="middle"
            style={{ fontFamily: "IBM Plex Mono", fontSize: 32, fill: "#f2efe6", fontWeight: 500 }}
          >
            {data.score}
          </text>
          <text
            x={100}
            y={120}
            textAnchor="middle"
            dominantBaseline="middle"
            style={{ fontFamily: "Inter", fontSize: 11, fill: "#9fb3ac", textTransform: "uppercase", letterSpacing: 1 }}
          >
            out of 100
          </text>
        </RadialBarChart>

        <div style={{ flex: 1, minWidth: 220 }}>
          <div className="stat-label">Summary</div>
          <p style={{ color: "var(--text)" }}>{data.summary}</p>
        </div>
      </div>

      <div className="card">
        <h2>Breakdown</h2>
        <table className="ledger">
          <tbody>
            {Object.entries(data.breakdown).map(([key, val]) => (
              <tr key={key}>
                <td style={{ textTransform: "capitalize" }}>{key.replace(/_/g, " ")}</td>
                <td className="num">{val} pts</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
