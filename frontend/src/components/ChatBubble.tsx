"use client";

import React from 'react';
import ReactMarkdown from 'react-markdown';
import { cn } from '@/lib/utils';
import { Message } from '@/types';
import { ChartRenderer } from './ChartRenderer';
import { Bot, User } from 'lucide-react';

interface ChatBubbleProps {
  message: Message;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({ message }) => {
  const isAssistant = message.role === 'assistant';

  return (
    <div className={cn("flex w-full mb-6", isAssistant ? "justify-start" : "justify-end")}>
      <div className={cn("flex max-w-[80%] md:max-w-[70%]", isAssistant ? "flex-row" : "flex-row-reverse")}>
        {/* Avatar */}
        <div className={cn(
          "flex items-center justify-center w-8 h-8 rounded-full shrink-0",
          isAssistant ? "bg-primary/20 text-primary mr-3" : "bg-white/10 text-white ml-3"
        )}>
          {isAssistant ? <Bot size={18} /> : <User size={18} />}
        </div>

        {/* Message Content */}
        <div className="flex flex-col w-full">
           <div className={cn(
             "p-4 rounded-2xl text-sm leading-relaxed",
             isAssistant 
               ? "bg-white/5 border border-white/5 text-gray-100 rounded-tl-none" 
               : "bg-primary text-primary-foreground rounded-tr-none"
           )}>
             <ReactMarkdown 
                components={{
                  code: ({node, ...props}) => <code className="bg-black/30 px-1 py-0.5 rounded text-xs font-mono" {...props} />
                }}
             >
               {message.content}
             </ReactMarkdown>
           </div>
           
           {/* Chart Rendering (Only for Assistant) */}
           {isAssistant && message.chartData && (
             <div className="mt-2 w-full animate-in fade-in zoom-in duration-300">
               <ChartRenderer data={message.chartData} />
             </div>
           )}
        </div>
      </div>
    </div>
  );
};
