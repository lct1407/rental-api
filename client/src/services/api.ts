/**
 * API Service Layer
 * Centralized service for making HTTP requests to the backend API
 */

interface RequestOptions {
  headers?: HeadersInit;
  body?: any;
}

interface ApiError {
  message: string;
  status: number;
  data?: any;
}

class ApiService {
  private baseURL: string;

  constructor() {
    // Use environment variable or fallback to empty string for mock mode
    this.baseURL = import.meta.env.VITE_API_URL || '';
  }

  /**
   * Get the authorization token from localStorage
   */
  private getAuthToken(): string | null {
    try {
      const authData = localStorage.getItem('auth');
      if (authData) {
        const parsed = JSON.parse(authData);
        return parsed.token || null;
      }
    } catch (error) {
      console.error('Error getting auth token:', error);
    }
    return null;
  }

  /**
   * Build headers for requests
   */
  private buildHeaders(customHeaders?: HeadersInit): HeadersInit {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // Merge custom headers
    if (customHeaders) {
      if (customHeaders instanceof Headers) {
        customHeaders.forEach((value, key) => {
          headers[key] = value;
        });
      } else if (Array.isArray(customHeaders)) {
        customHeaders.forEach(([key, value]) => {
          headers[key] = value;
        });
      } else {
        Object.assign(headers, customHeaders);
      }
    }

    const token = this.getAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  /**
   * Handle API response
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    const contentType = response.headers.get('content-type');
    const isJson = contentType?.includes('application/json');

    if (!response.ok) {
      const error: ApiError = {
        message: response.statusText,
        status: response.status,
      };

      if (isJson) {
        try {
          const errorData = await response.json();
          error.message = errorData.message || error.message;
          error.data = errorData;
        } catch (e) {
          // Ignore JSON parse errors
        }
      }

      throw error;
    }

    if (isJson) {
      return response.json();
    }

    return response.text() as any;
  }

  /**
   * Make a GET request
   */
  async get<T = any>(endpoint: string, options?: RequestOptions): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'GET',
      headers: this.buildHeaders(options?.headers),
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Make a POST request
   */
  async post<T = any>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers: this.buildHeaders(options?.headers),
      body: data ? JSON.stringify(data) : undefined,
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Make a PUT request
   */
  async put<T = any>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'PUT',
      headers: this.buildHeaders(options?.headers),
      body: data ? JSON.stringify(data) : undefined,
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Make a PATCH request
   */
  async patch<T = any>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'PATCH',
      headers: this.buildHeaders(options?.headers),
      body: data ? JSON.stringify(data) : undefined,
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Make a DELETE request
   */
  async delete<T = any>(endpoint: string, options?: RequestOptions): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'DELETE',
      headers: this.buildHeaders(options?.headers),
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Upload a file using FormData
   */
  async upload<T = any>(endpoint: string, formData: FormData, options?: RequestOptions): Promise<T> {
    const token = this.getAuthToken();
    const headers: HeadersInit = {
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options?.headers,
    };

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers,
      body: formData,
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Set a new base URL (useful for testing or switching environments)
   */
  setBaseURL(url: string): void {
    this.baseURL = url;
  }

  /**
   * Get the current base URL
   */
  getBaseURL(): string {
    return this.baseURL;
  }
}

// Export a singleton instance
export const apiService = new ApiService();

// Export the class for testing purposes
export { ApiService };

// Export types
export type { ApiError, RequestOptions };
