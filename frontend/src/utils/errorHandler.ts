/**
 * Centralized error handling utilities
 */

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: any;
}

export class AppError extends Error {
  public status?: number;
  public code?: string;
  public details?: any;

  constructor(message: string, status?: number, code?: string, details?: any) {
    super(message);
    this.name = 'AppError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

/**
 * Parse API error response
 */
export function parseApiError(error: any): ApiError {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response;
    return {
      message: data?.detail || data?.message || `HTTP ${status} Error`,
      status,
      code: data?.code,
      details: data
    };
  } else if (error.request) {
    // Network error
    return {
      message: 'Network error - please check your connection',
      code: 'NETWORK_ERROR'
    };
  } else {
    // Other error
    return {
      message: error.message || 'An unexpected error occurred',
      code: 'UNKNOWN_ERROR'
    };
  }
}

/**
 * Get user-friendly error message
 */
export function getUserFriendlyMessage(error: ApiError): string {
  switch (error.code) {
    case 'NETWORK_ERROR':
      return 'Unable to connect to the server. Please check your internet connection.';
    case 'AUTH_ERROR':
      return 'Authentication failed. Please log in again.';
    case 'PERMISSION_ERROR':
      return 'You do not have permission to perform this action.';
    case 'VALIDATION_ERROR':
      return 'Please check your input and try again.';
    case 'NOT_FOUND':
      return 'The requested resource was not found.';
    case 'CONFLICT':
      return 'This action conflicts with existing data.';
    default:
      return error.message || 'An unexpected error occurred. Please try again.';
  }
}

/**
 * Log error for debugging
 */
export function logError(error: any, context?: string): void {
  const timestamp = new Date().toISOString();
  const errorInfo = {
    timestamp,
    context,
    error: error instanceof Error ? {
      name: error.name,
      message: error.message,
      stack: error.stack
    } : error
  };
  
  console.error('Application Error:', errorInfo);
  
  // In production, you might want to send this to a logging service
  // sendToLoggingService(errorInfo);
}

/**
 * Handle API errors with user feedback
 */
export function handleApiError(error: any, context?: string): string {
  const apiError = parseApiError(error);
  const userMessage = getUserFriendlyMessage(apiError);
  
  logError(error, context);
  
  return userMessage;
}

/**
 * Retry function with exponential backoff
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> {
  let lastError: any;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      if (attempt === maxRetries) {
        break;
      }
      
      const delay = baseDelay * Math.pow(2, attempt);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError;
}

/**
 * Check if error is retryable
 */
export function isRetryableError(error: any): boolean {
  if (!error.response) return true; // Network errors are retryable
  
  const status = error.response.status;
  return status >= 500 || status === 429; // Server errors and rate limiting
}
