import axios from "axios";

import { clearSession, getAccessToken, refreshSession } from "./auth";

// Get CSRF token from cookies
const getCsrfToken = () => {
  return document.cookie.split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];
};

// Initialize CSRF token
const initCsrfToken = async () => {
  try {
    await axios.get('/api/v1/csrf/', { withCredentials: true });
  } catch (error) {
    console.warn('Failed to fetch CSRF token:', error);
  }
};

// Initialize CSRF token when module loads
initCsrfToken();

const api = axios.create({
  baseURL: "/api/v1",
  withCredentials: true
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  // Add CSRF token for unsafe methods
  if (config.method && !['get', 'head', 'options', 'trace'].includes(config.method.toLowerCase())) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      config.headers = config.headers ?? {};
      config.headers['X-CSRFToken'] = csrfToken;
    }
  }
  
  return config;
});

let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

const refreshAccessToken = async () => {
  if (!refreshPromise) {
    isRefreshing = true;
    refreshPromise = refreshSession()
      .then((tokens) => tokens?.access ?? null)
      .finally(() => {
        isRefreshing = false;
        refreshPromise = null;
      });
  }
  return refreshPromise;
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const status = error.response?.status;

    if (status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const newAccessToken = await refreshAccessToken();
        if (newAccessToken) {
          originalRequest.headers = originalRequest.headers ?? {};
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        if (!isRefreshing) {
          clearSession();
        }
      }
    }

    return Promise.reject(error);
  }
);

export default api;
