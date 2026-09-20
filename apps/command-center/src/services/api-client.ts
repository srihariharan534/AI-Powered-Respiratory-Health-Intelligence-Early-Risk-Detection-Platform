/**
 * Centralized API Client for NEXUS Command Center
 * Supports base URL, GET, POST, timeout, structured errors, and cancellation.
 */

import { ApiError } from '../types';

export interface RequestOptions {
  timeoutMs?: number;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

export class NexusApiClient {
  private baseUrl: string;
  private defaultTimeoutMs: number;

  constructor(baseUrl?: string, defaultTimeoutMs: number = 8000) {
    // Read from Vite env or fallback
    const metaEnv = typeof import.meta !== 'undefined' ? (import.meta as any).env : undefined;
    this.baseUrl = baseUrl || metaEnv?.VITE_API_BASE_URL || 'http://localhost:8000';
    this.defaultTimeoutMs = defaultTimeoutMs;
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  private async request<T>(
    endpoint: string,
    method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE',
    body?: unknown,
    options: RequestOptions = {}
  ): Promise<T> {

    const url = `${this.baseUrl}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const timeoutMs = options.timeoutMs ?? this.defaultTimeoutMs;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    // Combine external signal with timeout signal if provided
    if (options.signal) {
      options.signal.addEventListener('abort', () => controller.abort());
    }

    try {
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
          ...options.headers,
        },
        body: body !== undefined ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorData: any = {};
        try {
          errorData = await response.json();
        } catch {
          errorData = { message: response.statusText || 'Unknown server error' };
        }

        const apiError: ApiError = {
          status: response.status,
          message: errorData.message || errorData.detail || `HTTP ${response.status}: Request failed`,
          details: errorData,
          code: `HTTP_${response.status}`,
        };
        throw apiError;
      }

      // Handle 204 No Content
      if (response.status === 204) {
        return {} as T;
      }

      try {
        return (await response.json()) as T;
      } catch (err: any) {
        const parseError: ApiError = {
          status: response.status,
          message: 'Failed to parse JSON response from server',
          code: 'PARSE_ERROR',
        };
        throw parseError;
      }
    } catch (err: any) {
      clearTimeout(timeoutId);

      // Check if it was an abort/timeout
      if (controller.signal.aborted) {
        const timeoutError: ApiError = {
          status: 408,
          message: `Request timed out after ${timeoutMs}ms. Command center operating with limited connectivity.`,
          code: 'TIMEOUT',
        };
        throw timeoutError;
      }

      // If already an ApiError, rethrow
      if (err.status && err.message) {
        throw err;
      }

      // Otherwise network failure
      const networkError: ApiError = {
        status: 0,
        message: 'Unable to connect to the NEXUS API. The command center is operating with limited connectivity.',
        code: 'NETWORK_ERROR',
        details: { originalMessage: err.message },
      };
      throw networkError;
    }
  }

  public async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, 'GET', undefined, options);
  }

  public async post<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, 'POST', body, options);
  }

  public async patch<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, 'PATCH', body, options);
  }
}


export const apiClient = new NexusApiClient();
