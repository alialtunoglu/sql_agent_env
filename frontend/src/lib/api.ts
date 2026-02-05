import { ChatResponse } from '@/types';

const API_URL = 'http://localhost:8000/api/v1';
const SESSION_STORAGE_KEY = 'chat_session_id';

/**
 * Session ID'yi localStorage'dan al veya yeni oluştur
 */
export function getOrCreateSessionId(): string {
  if (typeof window === 'undefined') return ''; // SSR check
  
  let sessionId = localStorage.getItem(SESSION_STORAGE_KEY);
  
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  }
  
  return sessionId;
}

/**
 * Session'u sıfırla (yeni konuşma başlat)
 */
export function resetSession(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(SESSION_STORAGE_KEY);
}

export async function sendMessage(query: string, sessionId?: string): Promise<ChatResponse> {
  const activeSessionId = sessionId || getOrCreateSessionId();
  
  const response = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ 
      query,
      session_id: activeSessionId
    }),
  });

  if (!response.ok) {
    throw new Error('Network response was not ok');
  }

  return response.json();
}

/**
 * Upload CSV or Excel file
 */
export async function uploadFile(file: File, sessionId: string): Promise<any> {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_URL}/upload?session_id=${sessionId}`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'File upload failed');
  }

  return response.json();
}

/**
 * Get database status for session
 */
export async function getDatabaseStatus(sessionId: string): Promise<any> {
  const response = await fetch(`${API_URL}/database-status?session_id=${sessionId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to get database status');
  }

  return response.json();
}

/**
 * Delete user's uploaded database
 */
export async function deleteDatabase(sessionId: string): Promise<void> {
  const response = await fetch(`${API_URL}/database?session_id=${sessionId}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'Failed to delete database');
  }
}

/**
 * Execute user-approved SQL query
 */
export async function executeSql(sqlQuery: string, sessionId: string): Promise<any> {
  const response = await fetch(`${API_URL}/execute-sql`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      sql_query: sqlQuery,
      session_id: sessionId
    }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'SQL execution failed');
  }

  return response.json();
}
