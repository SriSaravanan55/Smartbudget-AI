import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import ProfileSetup from "./pages/ProfileSetup.jsx";
import LogExpense from "./pages/LogExpense.jsx";
import ExpenseHistory from "./pages/ExpenseHistory.jsx";
import Budget from "./pages/Budget.jsx";
import HealthScore from "./pages/HealthScore.jsx";
import Report from "./pages/Report.jsx";

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <ProfileSetup />
            </ProtectedRoute>
          }
        />
        <Route
          path="/expense"
          element={
            <ProtectedRoute>
              <LogExpense />
            </ProtectedRoute>
          }
        />
        <Route
          path="/expense-history"
          element={
            <ProtectedRoute>
              <ExpenseHistory />
            </ProtectedRoute>
          }
        />
        <Route
          path="/budget"
          element={
            <ProtectedRoute>
              <Budget />
            </ProtectedRoute>
          }
        />
        <Route
          path="/health-score"
          element={
            <ProtectedRoute>
              <HealthScore />
            </ProtectedRoute>
          }
        />
        <Route
          path="/report"
          element={
            <ProtectedRoute>
              <Report />
            </ProtectedRoute>
          }
        />

        <Route path="/" element={<Navigate to="/budget" replace />} />
        <Route path="*" element={<Navigate to="/budget" replace />} />
      </Routes>
    </AuthProvider>
  );
}
