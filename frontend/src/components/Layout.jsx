import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

const NAV_ITEMS = [
  { to: "/profile", label: "Profile Setup", index: "01" },
  { to: "/expense", label: "Log Expense", index: "02" },
  { to: "/expense-history", label: "Expense History", index: "03" },
  { to: "/budget", label: "Budget", index: "04" },
  { to: "/health-score", label: "Health Score", index: "05" },
  { to: "/report", label: "Full Report", index: "06" },
];

export default function Layout({ children }) {
  const { userId, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">$</span> SmartBudget AI
        </div>
        <div className="brand-sub">Personal ledger</div>

        <ul className="nav-list">
          {NAV_ITEMS.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                className={({ isActive }) => "nav-item" + (isActive ? " active" : "")}
              >
                <span className="nav-index">{item.index}</span>
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>

        <div className="sidebar-footer">
          <div className="user-chip">
            Signed in as <strong>{userId}</strong>
          </div>
          <button className="btn btn-ghost btn-block" onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </aside>

      <main className="main">{children}</main>
    </div>
  );
}
