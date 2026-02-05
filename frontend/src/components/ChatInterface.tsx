"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Send, RotateCcw } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { ChatBubble } from '@/components/ChatBubble';
import FileUpload from '@/components/FileUpload';
import { Message } from '@/types';
import { sendMessage, getOrCreateSessionId, resetSession } from '@/lib/api';

export const ChatInterface = () => {
  const [query, setQuery] = useState('');
  const [sessionId, setSessionId] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Merhaba! Ben sizin SQL Veri Analistinizim. Veritabanınızla ilgili herhangi bir soruyu sorabilirsiniz. Örn: "En çok satan 5 albüm hangisi?"'
    },
    {
      id: 'demo-query',
      role: 'user',
      content: '2023 yılında aylık satış trendlerini göster'
    },
    {
      id: 'demo-response',
      role: 'assistant',
      content: '2023 yılı için aylık satış verilerini analiz ettim. Aşağıda grafikte görüldüğü üzere, en yüksek satış Aralık ayında gerçekleşmiş.',
      chartData: [
        { name: 'Ocak', value: 4200 },
        { name: 'Şubat', value: 3800 },
        { name: 'Mart', value: 5100 },
        { name: 'Nisan', value: 4600 },
        { name: 'Mayıs', value: 5400 },
        { name: 'Haziran', value: 4900 },
        { name: 'Temmuz', value: 5800 },
        { name: 'Ağustos', value: 6200 },
        { name: 'Eylül', value: 5500 },
        { name: 'Ekim', value: 6800 },
        { name: 'Kasım', value: 7200 },
        { name: 'Aralık', value: 8900 }
      ]
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Session ID'yi initialize et
  useEffect(() => {
    setSessionId(getOrCreateSessionId());
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
        chartData: response.chart_data
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

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto p-4 md:p-6">
      {/* Header */}
      <header className="flex items-center justify-between mb-6 p-4 rounded-2xl glass animate-in fade-in slide-in-from-top-4 duration-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl flex items-center justify-center shadow-lg shadow-amber-900/20">
            <span className="text-white font-bold text-lg">⌘</span>
          </div>
          <div>
            <h1 className="text-xl font-semibold text-white tracking-tight">
              Data Analyst
            </h1>
            <p className="text-xs text-amber-500/80 flex items-center gap-1.5 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
              SQL Agent Active
            </p>
          </div>
        </div>
        <Button
          onClick={handleResetConversation}
          size="sm"
          className="bg-slate-700 hover:bg-slate-600 text-slate-300 hover:text-white transition-colors"
          title="Yeni konuşma başlat"
        >
          <RotateCcw size={16} className="mr-2" />
          Sıfırla
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
          <ChatBubble key={msg.id} message={msg} />
        ))}
        {isLoading && (
          <div className="flex justify-start mb-6">
             <div className="flex items-center gap-2 ml-14 bg-card px-4 py-3 rounded-2xl rounded-tl-none border border-amber-500/20">
                <span className="w-2 h-2 bg-amber-500 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                <span className="w-2 h-2 bg-orange-500 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                <span className="w-2 h-2 bg-red-500 rounded-full animate-bounce"></span>
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
