import axios from "axios";

const ACCESS_KEY = "shoshchat.token";
const REFRESH_KEY = "shoshchat.refresh";
const USER_KEY = "shoshchat.user";

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: {
    id: number | string;
    username: string;
    first_name?: string;
    last_name?: string;
    email?: string;
  };
}

export const getAccessToken = () => localStorage.getItem(ACCESS_KEY);
export const getRefreshToken = () => localStorage.getItem(REFRESH_KEY);

export const getStoredUser = () => {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch (error) {
    console.warn("Unable to parse stored user", error);
    return null;
  }
};

export const storeSession = (payload: AuthResponse | AuthTokens & { user?: unknown }) => {
  if ("user" in payload && payload.user) {
    localStorage.setItem(USER_KEY, JSON.stringify(payload.user));
  }
  localStorage.setItem(ACCESS_KEY, payload.access);
  localStorage.setItem(REFRESH_KEY, payload.refresh);
};

export const clearSession = () => {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
};

export const login = async (username: string, password: string) => {
  const response = await axios.post<AuthResponse>("/api/v1/auth/login/", {
    username,
    password,
  });
  storeSession(response.data);
  return response.data;
};

interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  password_confirm: string;
  first_name?: string;
  last_name?: string;
  company_name: string;
  industry: string;
  plan?: string;
  domain?: string;
  accent?: string;
  welcome_message?: string;
  primary_color?: string;
}

export const register = async (payload: RegisterPayload) => {
  await axios.post("/api/v1/auth/register/onboard/", payload);
};

export const refreshSession = async (): Promise<AuthTokens | null> => {
  const refresh = getRefreshToken();
  if (!refresh) {
    return null;
  }
  try {
    const response = await axios.post<{ access: string; refresh?: string }>(
      "/api/v1/auth/refresh/",
      { refresh }
    );
    const data = {
      access: response.data.access,
      refresh: response.data.refresh ?? refresh,
    };
    const user = getStoredUser();
    storeSession({ ...data, user });
    return data;
  } catch (error) {
    clearSession();
    throw error;
  }
};

export const hasSession = () => Boolean(getAccessToken());
