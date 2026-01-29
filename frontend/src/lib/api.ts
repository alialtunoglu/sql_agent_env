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
