"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Send, RotateCcw } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { ChatBubble } from '@/components/ChatBubble';
import FileUpload from '@/components/FileUpload';
import { Message } from '@/types';
import { sendMessage, getOrCreateSessionId, resetSession, getChatHistory } from '@/lib/api';

export const ChatInterface = () => {
  const [query, setQuery] = useState('');
  const [sessionId, setSessionId] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Merhaba! Ben sizin SQL Veri Analistinizim. Veritabanınızla ilgili herhangi bir soruyu sorabilirsiniz. Örn: "En çok satan 5 albüm hangisi?"'
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Session ID'yi initialize et ve chat history'yi yükle
  useEffect(() => {
    const initSession = async () => {
      const sid = getOrCreateSessionId();
      setSessionId(sid);
      
      // Redis'ten önceki mesajları çek
      try {
        const history = await getChatHistory(sid);
        
        if (history.messages && history.messages.length > 0) {
          console.log(`📚 Loaded ${history.count} messages from history`);
          
          // Backend'den gelen mesajları frontend formatına çevir
          const loadedMessages: Message[] = history.messages.map((msg: any, index: number) => ({
            id: `history-${index}`,
            role: msg.role,
            content: msg.content,
            // SQL query ve chart data parse edilebilir (gelecekte)
          }));
          
          setMessages(loadedMessages);
        } else {
          // Yeni session - welcome message göster
          setMessages([
            {
              id: 'welcome',
              role: 'assistant',
              content: 'Merhaba! Ben sizin SQL Veri Analistinizim. Veritabanınızla ilgili herhangi bir soruyu sorabilirsiniz. Örn: "En çok satan 5 albüm hangisi?"'
            }
          ]);
        }
      } catch (error) {
        console.error('Failed to load chat history:', error);
        // Hata durumunda welcome message göster
        setMessages([
          {
            id: 'welcome',
            role: 'assistant',
            content: 'Merhaba! Ben sizin SQL Veri Analistinizim. Veritabanınızla ilgili herhangi bir soruyu sorabilirsiniz.'
          }
        ]);
      }
    };
    
    initSession();
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleResetConversation = () => {
    resetSession();
    setSessionId(getOrCreateSessionId());
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: 'Merhaba! Ben sizin SQL Veri Analistinizim. Veritabanınızla ilgili herhangi bir soruyu sorabilirsiniz. Örn: "En çok satan 5 albüm hangisi?"'
      }
    ]);
  };

  const handleSend = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!query.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query
    };

    setMessages(prev => [...prev, userMessage]);
    setQuery('');
    setIsLoading(true);

    try {
      const response = await sendMessage(userMessage.content, sessionId);
      
      // Backend'den gelen session_id'yi güncelle
      if (response.session_id) {
        setSessionId(response.session_id);
      }
      
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        chartData: response.chart_data,
        sqlQuery: response.sql_query,
        requiresApproval: response.requires_approval
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };
  const handleResultMessage = (content: string, chartData?: any) => {
    const resultMessage: Message = {
      id: `result-${Date.now()}`,
      role: 'assistant',
      content: content,
      chartData: chartData
    };
    setMessages(prev => [...prev, resultMessage]);
  };
  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto p-4 md:p-6">
      {/* Header */}
      <header className="flex items-center justify-between mb-6 p-4 rounded-2xl glass animate-in fade-in slide-in-from-top-4 duration-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-md">
            <span className="text-white font-bold text-lg">📊</span>
          </div>
          <div>
            <h1 className="text-xl font-semibold text-gray-800 tracking-tight">
              Veri Analisti
            </h1>
            <p className="text-xs text-gray-500 flex items-center gap-1.5 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
              Çevrimiçi
            </p>
          </div>
        </div>
        <Button
          onClick={handleResetConversation}
          size="sm"
          className="bg-white hover:bg-gray-50 text-gray-700 border border-gray-200 hover:border-gray-300 transition-colors"
          title="Yeni konuşma başlat"
        >
          <RotateCcw size={16} className="mr-2" />
          Yeni Konuşma
        </Button>
      </header>

      {/* File Upload Section */}
      <div className="px-4 pt-4">
        <FileUpload sessionId={sessionId} onUploadSuccess={() => {
          // Optionally add a system message when upload succeeds
        }} />
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto mb-4 scrollbar-hide py-4 px-2">{messages.map((msg) => (
          <ChatBubble 
            key={msg.id} 
            message={msg}
            onResultMessage={handleResultMessage}
          />
        ))}
        {isLoading && (
          <div className="flex justify-start mb-6">
             <div className="flex items-center gap-2 ml-14 bg-white px-4 py-3 rounded-2xl rounded-tl-none border border-gray-200 shadow-sm">
                <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                <span className="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                <span className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></span>
             </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSend} className="relative mt-auto py-6 px-2">
        <div className="relative group">
          {/* Main container - high visibility */}
          <div className="relative flex items-center bg-slate-700 rounded-2xl border-2 border-slate-400 group-focus-within:border-orange-500 p-2 shadow-xl transition-all duration-300">
            <Input 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Verileriniz hakkında bir soru sorun..." 
              className="border-none bg-transparent h-14 text-lg focus-visible:ring-0 px-4 placeholder:text-slate-200 text-white w-full"
              disabled={isLoading}
            />
            <Button 
              type="submit" 
              size="md" 
              disabled={isLoading || !query.trim()}
              className={query.trim() 
                ? "bg-orange-500 hover:bg-orange-600 text-white h-12 w-12 rounded-xl shadow-lg transition-transform active:scale-95" 
                : "bg-slate-600 text-slate-300 h-12 w-12 rounded-xl border border-slate-400"
              }
            >
              <Send size={24} />
            </Button>
          </div>
        </div>
        <p className="text-center text-xs text-slate-500 mt-4 font-medium">
          AI generated answers can be imprecise.
        </p>
      </form>
    </div>
  );
};
