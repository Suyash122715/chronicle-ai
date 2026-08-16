export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface RegisterUserRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface RegisterUserResponse {
  user: User;
  message: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}
