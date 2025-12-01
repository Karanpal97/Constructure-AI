"use client";

import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import { Mail, User, Bot, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatDate } from "@/lib/utils";
import { Avatar } from "@/components/ui/avatar";
import { Card } from "@/components/ui/card";
import { LoadingDots } from "@/components/ui/loading";
import { ChatMessage as ChatMessageType } from "@/store/chat";
import { EmailSummary } from "@/lib/api";

interface ChatMessageProps {
  message: ChatMessageType;
  userPicture?: string | null;
}

export function ChatMessage({ message, userPicture }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        "flex gap-3",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <div className="flex-shrink-0">
        {isUser ? (
          <Avatar
            src={userPicture}
            fallback="You"
            size="sm"
            className="ring-2 ring-slate-700"
          />
        ) : (
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-violet-600 to-indigo-600 ring-2 ring-violet-500/30">
            <Bot className="h-4 w-4 text-white" />
          </div>
        )}
      </div>

      {/* Message Content */}
      <div
        className={cn(
          "flex max-w-[80%] flex-col gap-2",
          isUser ? "items-end" : "items-start"
        )}
      >
        <div
          className={cn(
            "rounded-2xl px-4 py-3",
            isUser
              ? "bg-gradient-to-r from-violet-600 to-indigo-600 text-white"
              : "bg-slate-800/80 text-slate-100 border border-slate-700/50"
          )}
        >
          {message.isLoading ? (
            <LoadingDots />
          ) : (
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown
                components={{
                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                  strong: ({ children }) => (
                    <strong className="font-semibold text-violet-300">{children}</strong>
                  ),
                  ul: ({ children }) => (
                    <ul className="my-2 ml-4 list-disc space-y-1">{children}</ul>
                  ),
                  li: ({ children }) => <li className="text-slate-300">{children}</li>,
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Email Cards */}
        {message.emails && message.emails.length > 0 && (
          <div className="mt-2 w-full space-y-2">
            {message.emails.map((emailSummary, index) => (
              <EmailCard
                key={emailSummary.email.id}
                emailSummary={emailSummary}
                index={index + 1}
              />
            ))}
          </div>
        )}

        {/* Timestamp */}
        <span className="flex items-center gap-1 text-xs text-slate-500">
          <Clock className="h-3 w-3" />
          {message.timestamp.toLocaleTimeString("en-US", {
            hour: "numeric",
            minute: "2-digit",
            hour12: true,
          })}
        </span>
      </div>
    </motion.div>
  );
}

function EmailCard({
  emailSummary,
  index,
}: {
  emailSummary: EmailSummary;
  index: number;
}) {
  const { email, summary } = emailSummary;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.1 }}
    >
      <Card variant="glass" className="p-4 hover:border-violet-500/50 transition-colors cursor-pointer">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500 to-teal-600">
            <Mail className="h-5 w-5 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <h4 className="font-medium text-white truncate">
                {email.subject || "(No Subject)"}
              </h4>
              <span className="flex-shrink-0 rounded-full bg-violet-500/20 px-2 py-0.5 text-xs font-medium text-violet-300">
                #{index}
              </span>
            </div>
            <p className="mt-0.5 text-sm text-slate-400 truncate">
              From: {email.sender} &lt;{email.sender_email}&gt;
            </p>
            <p className="mt-2 text-sm text-slate-300 line-clamp-2">
              {summary}
            </p>
            {email.is_unread && (
              <span className="mt-2 inline-flex items-center rounded-full bg-blue-500/20 px-2 py-0.5 text-xs font-medium text-blue-300">
                Unread
              </span>
            )}
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

