import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("sb_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Normalize FastAPI error shape { detail: "..." } into a plain message string.
export function extractError(err) {
  if (err.response?.data?.detail) {
    const detail = err.response.data.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((d) => d.msg).join(", ");
  }
  if (err.message === "Network Error") {
    return "Can't reach the backend. Is `uvicorn main:app --reload` running on port 8000?";
  }
  return "Something went wrong. Please try again.";
}

export default api;
