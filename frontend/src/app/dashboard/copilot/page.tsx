"use client";

import React, { useState, useRef, useEffect } from "react";
import { Sparkles, Send, Bot, User, ChevronDown, Wrench, Loader2 } from "lucide-react";
import { useChatStore } from "@/stores/chat-store";
import { cn } from "@/lib/utils";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function CopilotPage() {
  const { messages, sendMessage, isLoading } = useChatStore();
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    sendMessage(input);
    setInput("");
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col bg-card border border-border shadow-sm rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-muted/30 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Sparkles className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground leading-none">ReputationOS Copilot</h2>
            <p className="text-sm text-muted-foreground mt-1">Your AI Brand Assistant powered by Groq</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6 scroll-smooth" ref={scrollRef}>
        {messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center text-muted-foreground p-6">
            <Bot className="w-16 h-16 mb-4 opacity-20" />
            <h3 className="text-lg font-medium text-foreground mb-2">How can I help you today?</h3>
            <p className="text-sm max-w-md">I can help you analyze reviews, calculate reputation scores, and spot trends. Try asking one of the questions below.</p>
            <div className="mt-8 flex gap-4 w-full max-w-2xl justify-center">
              <button onClick={() => setInput("What is my current reputation score?")} className="text-sm p-4 rounded-xl border border-border bg-muted/20 hover:bg-muted text-left transition-colors flex-1 shadow-sm">
                "What is my current reputation score?"
              </button>
              <button onClick={() => setInput("Summarize my most recent reviews.")} className="text-sm p-4 rounded-xl border border-border bg-muted/20 hover:bg-muted text-left transition-colors flex-1 shadow-sm">
                "Summarize my most recent reviews."
              </button>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={cn("flex gap-4", msg.role === 'user' ? "flex-row-reverse" : "flex-row")}>
              <div className={cn("w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-sm", msg.role === 'user' ? "bg-primary text-primary-foreground" : "bg-accent border border-border text-foreground")}>
                {msg.role === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
              </div>
              <div className={cn("flex flex-col gap-2 max-w-[85%]", msg.role === 'user' ? "items-end" : "items-start")}>
                
                {/* Tool Calls */}
                {msg.tool_calls && msg.tool_calls.length > 0 && (
                  <div className="flex flex-col gap-1.5 w-full mb-1">
                    {msg.tool_calls.map((tc, idx) => (
                      <div key={idx} className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-muted/50 border border-border text-xs text-muted-foreground font-medium uppercase tracking-wider w-fit">
                        {tc.name === "get_reputation_score" ? <ChevronDown className="w-3.5 h-3.5 animate-pulse text-primary" /> : <Wrench className="w-3.5 h-3.5 animate-pulse text-primary" />}
                        Running Tool: {tc.name}
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Message Content */}
                {msg.content && (
                  <div className={cn(
                    "px-5 py-4 rounded-2xl text-sm leading-relaxed shadow-sm",
                    msg.role === 'user' 
                      ? "bg-primary text-primary-foreground rounded-tr-none" 
                      : "bg-muted border border-border text-foreground rounded-tl-none prose prose-sm dark:prose-invert max-w-none"
                  )}>
                    {msg.role === 'user' ? (
                      msg.content
                    ) : (
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={{
                          table: ({node, ...props}) => <div className="overflow-x-auto my-4"><table className="min-w-full divide-y divide-border border border-border rounded-md" {...props} /></div>,
                          th: ({node, ...props}) => <th className="px-3 py-2 bg-background font-semibold text-left border-b border-border" {...props} />,
                          td: ({node, ...props}) => <td className="px-3 py-2 border-t border-border" {...props} />,
                          p: ({node, ...props}) => <p className="last:mb-0" {...props} />
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    )}
                  </div>
                )}

                {msg.isStreaming && !msg.content && (!msg.tool_calls || msg.tool_calls.length === 0) && (
                  <div className="px-5 py-4 rounded-2xl bg-muted border border-border rounded-tl-none flex items-center justify-center shadow-sm">
                    <Loader2 className="w-5 h-5 animate-spin text-primary" />
                    <span className="ml-2 text-sm text-muted-foreground">Thinking...</span>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Input */}
      <div className="p-4 bg-card border-t border-border">
        <form onSubmit={handleSubmit} className="relative flex items-center max-w-4xl mx-auto">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Message ReputationOS Copilot..."
            className="w-full bg-muted/40 border border-border rounded-full pl-6 pr-14 py-3.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all shadow-sm"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="absolute right-2 p-2 rounded-full bg-primary text-primary-foreground disabled:opacity-50 hover:bg-primary/90 transition-all hover:scale-105 active:scale-95 shadow-sm"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
