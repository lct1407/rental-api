/**
 * User Service
 * Example service demonstrating how to use the API service layer
 * Replace mock data imports with these service calls when backend is ready
 */

import { apiService } from './api';
import type { User, UserStatus } from '../types';

interface LoginCredentials {
  email: string;
  password: string;
}

interface RegisterData {
  name: string;
  email: string;
  password: string;
}

interface AuthResponse {
  user: User;
  token: string;
}

interface UpdateUserData {
  name?: string;
  email?: string;
  phone?: string;
  status?: UserStatus;
}

interface PasswordChangeData {
  currentPassword: string;
  newPassword: string;
}

/**
 * User Service
 * Handles all user-related API operations
 */
export const userService = {
  /**
   * Authenticate user with email and password
   */
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    return apiService.post<AuthResponse>('/auth/login', credentials);
  },

  /**
   * Register a new user
   */
  async register(data: RegisterData): Promise<AuthResponse> {
    return apiService.post<AuthResponse>('/auth/register', data);
  },

  /**
   * Logout current user
   */
  async logout(): Promise<void> {
    return apiService.post('/auth/logout');
  },

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    return apiService.get<User>('/users/me');
  },

  /**
   * Get all users (admin only)
   */
  async getAllUsers(): Promise<User[]> {
    return apiService.get<User[]>('/users');
  },

  /**
   * Get a specific user by ID
   */
  async getUserById(id: string): Promise<User> {
    return apiService.get<User>(`/users/${id}`);
  },

  /**
   * Update user profile
   */
  async updateUser(id: string, data: UpdateUserData): Promise<User> {
    return apiService.patch<User>(`/users/${id}`, data);
  },

  /**
   * Update current user's profile
   */
  async updateProfile(data: UpdateUserData): Promise<User> {
    return apiService.patch<User>('/users/me', data);
  },

  /**
   * Change user password
   */
  async changePassword(data: PasswordChangeData): Promise<void> {
    return apiService.post('/users/me/password', data);
  },

  /**
   * Delete a user (admin only)
   */
  async deleteUser(id: string): Promise<void> {
    return apiService.delete(`/users/${id}`);
  },

  /**
   * Update user credits (admin only)
   */
  async updateCredits(userId: string, credits: number): Promise<User> {
    return apiService.patch<User>(`/users/${userId}/credits`, { credits });
  },

  /**
   * Regenerate user's API key
   */
  async regenerateApiKey(userId: string): Promise<{ apiKey: string }> {
    return apiService.post<{ apiKey: string }>(`/users/${userId}/api-key/regenerate`);
  },

  /**
   * Update user status (admin only)
   */
  async updateStatus(userId: string, status: UserStatus): Promise<User> {
    return apiService.patch<User>(`/users/${userId}/status`, { status });
  },

  /**
   * Search users by query (admin only)
   */
  async searchUsers(query: string): Promise<User[]> {
    return apiService.get<User[]>(`/users/search?q=${encodeURIComponent(query)}`);
  },

  /**
   * Upload user avatar
   */
  async uploadAvatar(file: File): Promise<{ avatarUrl: string }> {
    const formData = new FormData();
    formData.append('avatar', file);
    return apiService.upload<{ avatarUrl: string }>('/users/me/avatar', formData);
  },
};
