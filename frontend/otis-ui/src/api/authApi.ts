import axios from "axios";

export function resolveApiBaseUrl(envValue?: string): string {
  return envValue && envValue.trim() ? envValue : "/";
}

const API_BASE_URL = resolveApiBaseUrl(import.meta.env.VITE_API_BASE_URL);

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem("refresh_token");
  if (!refreshToken) {
    return null;
  }

  const res = await axios.post(
    `${API_BASE_URL}/v1/auth/refresh`,
    { refresh_token: refreshToken },
    { withCredentials: true },
  );

  localStorage.setItem("access_token", res.data.access_token);
  if (res.data.refresh_token) {
    localStorage.setItem("refresh_token", res.data.refresh_token);
  }
  return res.data.access_token as string;
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as
      | (typeof error.config & { _retry?: boolean })
      | undefined;

    if (
      error.response?.status !== 401 ||
      !originalRequest ||
      originalRequest._retry ||
      originalRequest.url?.includes("/v1/auth/login") ||
      originalRequest.url?.includes("/v1/auth/refresh")
    ) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    if (!isRefreshing) {
      isRefreshing = true;
      refreshPromise = refreshAccessToken()
        .catch(() => null)
        .finally(() => {
          isRefreshing = false;
          refreshPromise = null;
        });
    }

    const newToken = await refreshPromise;
    if (!newToken) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      return Promise.reject(error);
    }

    originalRequest.headers = {
      ...originalRequest.headers,
      Authorization: `Bearer ${newToken}`,
    };
    return api(originalRequest);
  },
);

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
  if (res.data.refresh_token) {
    localStorage.setItem("refresh_token", res.data.refresh_token);
  }

  return res.data;
}

export async function fetchMe() {
  const res = await api.get("/v1/auth/me");
  return res.data;
}

export async function logout() {
  try {
    await api.post("/v1/auth/logout");
  } catch {
    // Ignore logout failures; clear local tokens regardless.
  }
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

export default api;
