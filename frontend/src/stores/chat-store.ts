import { create } from 'zustand';
import { api } from '@/lib/api';
import { useTenantStore } from './tenant-store';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'tool';
  content: string;
  tool_calls?: { name: string }[];
  isStreaming?: boolean;
}

interface ChatState {
  isOpen: boolean;
  messages: ChatMessage[];
  sessionId: string | null;
  isLoading: boolean;
  toggleChat: () => void;
  setIsOpen: (open: boolean) => void;
  addMessage: (msg: ChatMessage) => void;
  updateLastMessage: (content: string, isStreaming?: boolean) => void;
  appendToolCall: (name: string) => void;
  sendMessage: (text: string, isWidget?: boolean, clientId?: string) => Promise<void>;
  clearChat: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  isOpen: false,
  messages: [],
  sessionId: null,
  isLoading: false,

  toggleChat: () => set((state) => ({ isOpen: !state.isOpen })),
  setIsOpen: (open) => set({ isOpen: open }),
  
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  
  updateLastMessage: (content, isStreaming = false) => set((state) => {
    const newMessages = [...state.messages];
    if (newMessages.length > 0) {
      const lastIdx = newMessages.length - 1;
      newMessages[lastIdx] = { 
        ...newMessages[lastIdx], 
        content: newMessages[lastIdx].content + content,
        isStreaming
      };
    }
    return { messages: newMessages };
  }),

  appendToolCall: (name) => set((state) => {
    const newMessages = [...state.messages];
    if (newMessages.length > 0) {
      const lastIdx = newMessages.length - 1;
      const lastMsg = newMessages[lastIdx];
      newMessages[lastIdx] = {
        ...lastMsg,
        tool_calls: [...(lastMsg.tool_calls || []), { name }]
      };
    }
    return { messages: newMessages };
  }),

  clearChat: () => set({ messages: [], sessionId: null }),

  sendMessage: async (text: string, isWidget = false, clientId?: string) => {
    const { sessionId, addMessage, updateLastMessage, appendToolCall } = get();
    
    // Add user message
    const userMsgId = Date.now().toString();
    addMessage({ id: userMsgId, role: 'user', content: text });
    set({ isLoading: true });
    
    // Add placeholder assistant message
    const astMsgId = (Date.now() + 1).toString();
    addMessage({ id: astMsgId, role: 'assistant', content: '', isStreaming: true });

    try {
      const endpoint = isWidget ? `/api/chat/widget/${clientId}` : '/api/chat/manager';
      
      let token = null;
      if (typeof window !== "undefined") {
        const authData = localStorage.getItem("auth-storage");
        if (authData) {
          try {
            token = JSON.parse(authData).state?.token;
          } catch (e) {}
        }
      }
      
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (!isWidget && token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(baseUrl + endpoint, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          session_id: sessionId,
          message: text,
          location_id: !isWidget ? useTenantStore.getState().currentLocation?.id : undefined,
          location_name: !isWidget ? useTenantStore.getState().currentLocation?.name : undefined
        })
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
                set({ sessionId: data.session_id });
              } else if (data.type === 'tool_call') {
                appendToolCall(data.name);
              } else if (data.type === 'message') {
                updateLastMessage(data.content, false); // Assuming it streams chunks or just whole message. The backend yields the whole message right now.
              }
            } catch (e) {
              console.error("Failed to parse chat chunk", e);
            }
          }
        }
      }
    } catch (error) {
      console.error("Chat error:", error);
      updateLastMessage("\n\n*Error: Could not connect to AI Copilot.*", false);
    } finally {
      set({ isLoading: false });
      // Finalize streaming state
      set((state) => {
        const newMessages = [...state.messages];
        if (newMessages.length > 0) {
          newMessages[newMessages.length - 1].isStreaming = false;
        }
        return { messages: newMessages };
      });
    }
  }
}));
