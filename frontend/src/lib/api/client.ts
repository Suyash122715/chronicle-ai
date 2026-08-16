import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { ApiError, ApiErrorDetail } from "@/types/api";
import { getStoredToken, useAuthStore } from "@/stores/authStore";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request Interceptor: Attach Bearer Token if present
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getStoredToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Parse Backend `{ "detail": "..." }` Errors
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorDetail>) => {
    const status = error.response?.status || 500;
    let message = "An unexpected error occurred.";

    if (error.response?.data?.detail) {
      message = error.response.data.detail;
    } else if (error.message) {
      message = error.message;
    }

    if (status === 401) {
      // Clear invalid token from store if 401 received
      if (typeof window !== "undefined") {
        useAuthStore.getState().clearAuth();
      }
    }

    return Promise.reject(new ApiError(status, message));
  }
);

export default apiClient;
