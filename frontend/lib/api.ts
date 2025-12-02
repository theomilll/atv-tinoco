/**
 * API client utility for making authenticated requests to the backend.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface FetchOptions extends RequestInit {
  body?: any;
}

/**
 * Get CSRF token from cookies
 */
function getCsrfToken(): string | null {
  if (typeof document === 'undefined') return null;
  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    cookie = cookie.trim();
    if (cookie.startsWith(name + '=')) {
      return cookie.substring(name.length + 1);
    }
  }
  return null;
}

/**
 * Make an authenticated API request
 */
async function apiRequest<T = any>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Add CSRF token for non-GET requests
  if (options.method && options.method !== 'GET') {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      headers['X-CSRFToken'] = csrfToken;
    }
  }

  const config: RequestInit = {
    ...options,
    headers,
    credentials: 'include', // Include cookies
  };

  // Stringify body if it's an object
  if (options.body && typeof options.body === 'object') {
    config.body = JSON.stringify(options.body);
  }

  const response = await fetch(url, config);

  // Handle 401 - throw error (let components handle redirect via useAuth)
  if (response.status === 401) {
    throw new Error('Unauthorized');
  }

  // Handle other errors
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Request failed' }));
    throw new Error(errorData.error || `Request failed with status ${response.status}`);
  }

  // Return JSON response
  return response.json();
}

// Auth API
export const auth = {
  async me() {
    return apiRequest<{ id: number; username: string; email: string }>('/api/auth/me/');
  },

  async login(username: string, password: string) {
    return apiRequest('/api/auth/login/', {
      method: 'POST',
      body: { username, password },
    });
  },

  async logout() {
    return apiRequest('/api/auth/logout/', { method: 'POST' });
  },
};

// Conversation API
export interface MessageAttachment {
  filename: string;
  file_type: string;
  file_path: string;
  category: 'image' | 'document';
}

export interface Message {
  id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
  citations?: Array<{
    document_title: string;
    chunk_content: string;
    relevance_score: number;
    chunk_index: number;
  }>;
  attachments?: MessageAttachment[];
}

export interface Conversation {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  messages?: Message[];
}

export interface SendMessageResponse {
  user_message: Message;
  assistant_message: Message;
}

// Document API
export interface Document {
  id: number;
  title: string;
  file: string;
  file_type: string;
  file_size: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  chunk_count: number;
}

export interface DocumentChunk {
  id: number;
  chunk_index: number;
  content: string;
  metadata: Record<string, any>;
  created_at: string;
}

export interface DocumentDetail extends Document {
  chunks: DocumentChunk[];
}

export const documents = {
  async list(params?: { search?: string; status?: string }) {
    let endpoint = '/api/documents/';
    const queryParams = new URLSearchParams();
    if (params?.search) queryParams.append('search', params.search);
    if (params?.status) queryParams.append('status', params.status);
    const query = queryParams.toString();
    if (query) endpoint += `?${query}`;

    const response = await apiRequest<{ results: Document[] }>(endpoint);
    return response.results || [];
  },

  async get(id: number) {
    return apiRequest<DocumentDetail>(`/api/documents/${id}/`);
  },

  async upload(file: File, title?: string) {
    const formData = new FormData();
    formData.append('file', file);
    if (title) formData.append('title', title);

    const url = `${API_BASE_URL}/api/documents/`;
    const csrfToken = getCsrfToken();

    const response = await fetch(url, {
      method: 'POST',
      credentials: 'include',
      headers: csrfToken ? { 'X-CSRFToken': csrfToken } : {},
      body: formData,
    });

    if (response.status === 401) {
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Upload failed' }));
      throw new Error(errorData.error || `Upload failed with status ${response.status}`);
    }

    return response.json() as Promise<Document>;
  },

  async fromUrl(url: string, title?: string) {
    return apiRequest<Document>('/api/documents/from-url/', {
      method: 'POST',
      body: { url, title: title || '' },
    });
  },

  async delete(id: number) {
    return apiRequest(`/api/documents/${id}/`, { method: 'DELETE' });
  },

  async reprocess(id: number) {
    return apiRequest<Document>(`/api/documents/${id}/reprocess/`, { method: 'POST' });
  },
};

// Streaming callback types
export interface StreamCallbacks {
  onUserMessage?: (message: Message) => void;
  onChunk?: (content: string) => void;
  onAssistantMessage?: (message: Message) => void;
  onError?: (error: string) => void;
  onDone?: () => void;
}

export const conversations = {
  async list(search?: string) {
    let endpoint = '/api/conversations/';
    if (search) {
      endpoint += `?q=${encodeURIComponent(search)}`;
    }
    const response = await apiRequest<{ results: Conversation[] }>(endpoint);
    return response.results || [];
  },

  async get(id: number) {
    return apiRequest<Conversation>(`/api/conversations/${id}/`);
  },

  async create(title: string = '') {
    return apiRequest<Conversation>('/api/conversations/', {
      method: 'POST',
      body: { title },
    });
  },

  async delete(id: number) {
    return apiRequest(`/api/conversations/${id}/`, { method: 'DELETE' });
  },

  async update(id: number, data: { title?: string }) {
    return apiRequest<Conversation>(`/api/conversations/${id}/`, {
      method: 'PATCH',
      body: data,
    });
  },

  async sendMessage(conversationId: number, content: string, files?: File[]) {
    // Use FormData if files are present
    if (files && files.length > 0) {
      const formData = new FormData();
      formData.append('content', content);
      files.forEach(file => formData.append('files', file));

      const url = `${API_BASE_URL}/api/conversations/${conversationId}/messages/`;
      const csrfToken = getCsrfToken();

      const response = await fetch(url, {
        method: 'POST',
        credentials: 'include',
        headers: csrfToken ? { 'X-CSRFToken': csrfToken } : {},
        body: formData,
      });

      if (response.status === 401) {
        throw new Error('Unauthorized');
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Request failed' }));
        throw new Error(errorData.error || `Request failed with status ${response.status}`);
      }

      return response.json() as Promise<SendMessageResponse>;
    }

    // JSON path for text-only
    return apiRequest<SendMessageResponse>(
      `/api/conversations/${conversationId}/messages/`,
      {
        method: 'POST',
        body: { content },
      }
    );
  },

  async sendMessageStream(
    conversationId: number,
    content: string,
    callbacks: StreamCallbacks
  ): Promise<void> {
    const url = `${API_BASE_URL}/api/conversations/${conversationId}/messages/stream/`;
    const csrfToken = getCsrfToken();

    const response = await fetch(url, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
      },
      body: JSON.stringify({ content }),
    });

    if (response.status === 401) {
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Request failed' }));
      throw new Error(errorData.error || `Request failed with status ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete SSE events
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      let eventType = '';
      let eventData = '';

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          eventType = line.slice(7);
        } else if (line.startsWith('data: ')) {
          eventData = line.slice(6);

          if (eventType && eventData) {
            try {
              const data = JSON.parse(eventData);

              switch (eventType) {
                case 'user_message':
                  callbacks.onUserMessage?.(data);
                  break;
                case 'chunk':
                  callbacks.onChunk?.(data.content);
                  break;
                case 'assistant_message':
                  callbacks.onAssistantMessage?.(data);
                  break;
                case 'error':
                  callbacks.onError?.(data.error);
                  break;
                case 'done':
                  callbacks.onDone?.();
                  break;
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }

          eventType = '';
          eventData = '';
        }
      }
    }
  },
};
