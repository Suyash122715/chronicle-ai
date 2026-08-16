import apiClient from "@/lib/api/client";
import {
  LoginRequest,
  RegisterUserRequest,
  RegisterUserResponse,
  TokenResponse,
  User,
} from "@/types/auth";

export const authService = {
  async register(payload: RegisterUserRequest): Promise<RegisterUserResponse> {
    const response = await apiClient.post<RegisterUserResponse>("/auth/register", payload);
    return response.data;
  },

  async login(payload: LoginRequest): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>("/auth/login", payload);
    return response.data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>("/users/me");
    return response.data;
  },
};

export default authService;
