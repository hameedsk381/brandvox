"use client";

import React, { useState, useRef, useEffect } from "react";
import { MessageSquare, X, Send, Bot, User, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

// This simulates a standalone widget store
function useWidgetChat(clientId: string) {
  const [messages, setMessages] = useState<any[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (text: string) => {
    const userMsg = { id: Date.now().toString(), role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    const astMsgId = (Date.now() + 1).toString();
    setMessages(prev => [...prev, { id: astMsgId, role: 'assistant', content: '', isStreaming: true }]);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/chat/widget/${clientId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, message: text })
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      let done = false;
      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        
        if (value) {
          const chunkStr = decoder.decode(value, { stream: true });
          const lines = chunkStr.split('\n').filter(l => l.trim() !== '');
          
          for (const line of lines) {
            try {
              const data = JSON.parse(line);
              if (data.type === 'session_id') {
                setSessionId(data.session_id);
              } else if (data.type === 'message') {
                setMessages(prev => {
                  const newMsgs = [...prev];
                  const last = newMsgs[newMsgs.length - 1];
                  newMsgs[newMsgs.length - 1] = { ...last, content: last.content + data.content };
                  return newMsgs;
                });
              }
            } catch (e) {}
          }
        }
      }
    } catch (error) {
      setMessages(prev => {
        const newMsgs = [...prev];
        const last = newMsgs[newMsgs.length - 1];
        newMsgs[newMsgs.length - 1] = { ...last, content: "Error connecting to support." };
        return newMsgs;
      });
    } finally {
      setIsLoading(false);
      setMessages(prev => {
        const newMsgs = [...prev];
        if (newMsgs.length > 0) newMsgs[newMsgs.length - 1].isStreaming = false;
        return newMsgs;
      });
    }
  };

  return { messages, sendMessage, isLoading };
}

interface CustomerWidgetProps {
  clientId: string;
  brandName?: string;
  primaryColor?: string;
}

export function CustomerWidget({ clientId, brandName = "Support", primaryColor = "hsl(var(--primary))" }: CustomerWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const { messages, sendMessage, isLoading } = useWidgetChat(clientId);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    sendMessage(input);
    setInput("");
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {/* Chat Window */}
      <div
        className={cn(
          "mb-4 w-[350px] h-[500px] flex flex-col bg-background border border-border shadow-2xl rounded-2xl overflow-hidden transition-all duration-300 origin-bottom-right",
          isOpen ? "scale-100 opacity-100" : "scale-75 opacity-0 pointer-events-none absolute bottom-16 right-0"
        )}
      >
        {/* Header */}
        <div 
          className="flex items-center justify-between px-4 py-4"
          style={{ backgroundColor: primaryColor }}
        >
          <div className="flex items-center gap-2 text-white">
            <Bot className="w-5 h-5" />
            <div>
              <h3 className="text-sm font-semibold leading-none">{brandName} Assistant</h3>
              <p className="text-xs opacity-80 mt-1">We typically reply instantly</p>
            </div>
          </div>
          <button onClick={() => setIsOpen(false)} className="text-white/80 hover:text-white transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 scroll-smooth" ref={scrollRef}>
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center text-muted-foreground p-6">
              <MessageSquare className="w-12 h-12 mb-4 opacity-20" />
              <p className="text-sm">Hi! I'm here to help. How can I assist you today?</p>
            </div>
          ) : (
            messages.map((msg) => (
              <div key={msg.id} className={cn("flex gap-2 max-w-[85%]", msg.role === 'user' ? "self-end flex-row-reverse" : "self-start flex-row")}>
                <div className={cn("w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-1", msg.role === 'user' ? "bg-muted text-muted-foreground hidden" : "bg-muted text-muted-foreground")}>
                  {msg.role === 'assistant' && <Bot className="w-3 h-3" />}
                </div>
                <div className={cn("px-3 py-2 rounded-2xl text-sm whitespace-pre-wrap leading-relaxed", 
                  msg.role === 'user' 
                    ? "bg-primary text-primary-foreground rounded-tr-sm" 
                    : "bg-muted text-foreground rounded-tl-sm"
                )}>
                  {msg.content}
                  {msg.isStreaming && !msg.content && <Loader2 className="w-4 h-4 animate-spin opacity-50" />}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Input */}
        <div className="p-3 bg-background border-t border-border">
          <form onSubmit={handleSubmit} className="relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message..."
              className="w-full bg-muted border-transparent rounded-full pl-4 pr-12 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary focus:bg-background transition-all"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="absolute right-1.5 p-1.5 rounded-full text-primary disabled:opacity-50 hover:bg-muted transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <div className="text-center mt-2">
            <span className="text-[10px] text-muted-foreground">Powered by ReputationOS AI</span>
          </div>
        </div>
      </div>

      {/* Floating Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "p-4 rounded-full shadow-lg transition-transform hover:scale-105 active:scale-95",
          isOpen ? "rotate-90 opacity-0 pointer-events-none absolute" : "rotate-0 opacity-100"
        )}
        style={{ backgroundColor: primaryColor, color: "white" }}
      >
        <MessageSquare className="w-6 h-6" />
      </button>
    </div>
  );
}
