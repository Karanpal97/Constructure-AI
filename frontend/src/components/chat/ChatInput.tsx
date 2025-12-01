"use client";

import { useState, useRef, KeyboardEvent } from "react";
import { motion } from "framer-motion";
import { Send, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

const suggestions = [
  "Show me my last 5 emails",
  "Reply to email 1",
  "Delete email from promotions",
  "Give me today's digest",
];

export function ChatInput({ onSend, isLoading, disabled }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (message.trim() && !isLoading && !disabled) {
      onSend(message.trim());
      setMessage("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`;
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setMessage(suggestion);
    textareaRef.current?.focus();
  };

  return (
    <div className="space-y-3">
      {/* Quick Suggestions */}
      <div className="flex flex-wrap gap-2">
        {suggestions.map((suggestion, index) => (
          <motion.button
            key={suggestion}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            onClick={() => handleSuggestionClick(suggestion)}
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium",
              "bg-slate-800/50 text-slate-400 border border-slate-700/50",
              "hover:bg-slate-800 hover:text-slate-200 hover:border-violet-500/50",
              "transition-all duration-200"
            )}
            disabled={isLoading || disabled}
          >
            <Sparkles className="h-3 w-3 text-violet-400" />
            {suggestion}
          </motion.button>
        ))}
      </div>

      {/* Input Area */}
      <div className="relative">
        <div
          className={cn(
            "flex items-end gap-2 rounded-2xl border bg-slate-900/80 p-3",
            "border-slate-700/50 focus-within:border-violet-500/50",
            "transition-all duration-200"
          )}
        >
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            placeholder="Ask me anything about your emails..."
            rows={1}
            disabled={isLoading || disabled}
            className={cn(
              "flex-1 resize-none bg-transparent text-white placeholder:text-slate-500",
              "focus:outline-none disabled:opacity-50",
              "min-h-[44px] max-h-[200px]"
            )}
          />
          <Button
            onClick={handleSend}
            disabled={!message.trim() || isLoading || disabled}
            size="sm"
            className="flex-shrink-0"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <svg
                  className="h-4 w-4 animate-spin"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Thinking...
              </span>
            ) : (
              <>
                <Send className="h-4 w-4" />
                Send
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

