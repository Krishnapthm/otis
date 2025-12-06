import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export async function signup(data: {
  email: string;
  password: string;
  uname: string;
}) {
  const res = await api.post("/v1/auth/register", data);
  return res.data;
}

export async function login(email: string, password: string) {
  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);

  const res = await api.post("/v1/auth/login", body, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });

  localStorage.setItem("access_token", res.data.access_token);

  return res.data;
}

export async function fetchMe() {
  const res = await api.get("/v1/auth/me");
  return res.data;
}

export function logout() {
  localStorage.removeItem("access_token");
}

export default api;
