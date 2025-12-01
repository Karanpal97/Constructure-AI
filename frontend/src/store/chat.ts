import { create } from "zustand";
import { api, ChatResponse, EmailSummary, EmailResponse } from "@/lib/api";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  isLoading?: boolean;
  emails?: EmailSummary[];
  suggestedReplies?: EmailResponse[];
  actionType?: string;
}

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  recentEmails: EmailSummary[];
  
  sendMessage: (content: string) => Promise<void>;
  initializeChat: () => Promise<void>;
  clearChat: () => void;
  clearError: () => void;
}

let messageIdCounter = 0;
const generateId = () => `msg_${++messageIdCounter}_${Date.now()}`;

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isLoading: false,
  error: null,
  recentEmails: [],

  initializeChat: async () => {
    try {
      set({ isLoading: true });
      
      const { message } = await api.getWelcomeMessage();
      
      const welcomeMessage: ChatMessage = {
        id: generateId(),
        role: "assistant",
        content: message,
        timestamp: new Date(),
      };
      
      set({ messages: [welcomeMessage], isLoading: false });
    } catch (error) {
      console.error("Chat initialization error:", error);
      
      // Fallback welcome message
      const fallbackMessage: ChatMessage = {
        id: generateId(),
        role: "assistant",
        content: "👋 Welcome! I'm your AI email assistant. I can help you read, reply to, and manage your emails. Try saying **\"Show me my last 5 emails\"** to get started!",
        timestamp: new Date(),
      };
      
      set({ messages: [fallbackMessage], isLoading: false });
    }
  },

  sendMessage: async (content: string) => {
    const { messages } = get();
    
    // Add user message
    const userMessage: ChatMessage = {
      id: generateId(),
      role: "user",
      content,
      timestamp: new Date(),
    };
    
    // Add loading message
    const loadingMessage: ChatMessage = {
      id: generateId(),
      role: "assistant",
      content: "",
      timestamp: new Date(),
      isLoading: true,
    };
    
    set({ 
      messages: [...messages, userMessage, loadingMessage],
      isLoading: true,
      error: null,
    });
    
    try {
      const response = await api.sendChatMessage(content);
      
      const assistantMessage: ChatMessage = {
        id: generateId(),
        role: "assistant",
        content: response.message,
        timestamp: new Date(),
        emails: response.emails,
        suggestedReplies: response.suggested_replies,
        actionType: response.action_type,
      };
      
      // Update recent emails if we got some
      const newRecentEmails = response.emails 
        ? response.emails 
        : get().recentEmails;
      
      // Replace loading message with actual response
      set(state => ({
        messages: [
          ...state.messages.slice(0, -1),
          assistantMessage,
        ],
        isLoading: false,
        recentEmails: newRecentEmails,
      }));
      
    } catch (error) {
      console.error("Send message error:", error);
      
      const errorMessage: ChatMessage = {
        id: generateId(),
        role: "assistant",
        content: "Sorry, I encountered an error processing your request. Please try again.",
        timestamp: new Date(),
        actionType: "error",
      };
      
      set(state => ({
        messages: [
          ...state.messages.slice(0, -1),
          errorMessage,
        ],
        isLoading: false,
        error: error instanceof Error ? error.message : "An error occurred",
      }));
    }
  },

  clearChat: () => {
    set({ messages: [], recentEmails: [], error: null });
    get().initializeChat();
  },

  clearError: () => set({ error: null }),
}));

