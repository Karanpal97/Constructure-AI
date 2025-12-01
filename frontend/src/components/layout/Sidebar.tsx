"use client";

import { motion } from "framer-motion";
import {
  Mail,
  Inbox,
  Send,
  Trash2,
  FolderOpen,
  Calendar,
  Star,
  Archive,
  Settings,
  HelpCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

const menuItems = [
  { icon: Inbox, label: "Inbox", badge: 12, active: true },
  { icon: Star, label: "Starred", badge: 0 },
  { icon: Send, label: "Sent", badge: 0 },
  { icon: Archive, label: "Archive", badge: 0 },
  { icon: Trash2, label: "Trash", badge: 0 },
];

const categories = [
  { icon: FolderOpen, label: "Work", color: "bg-blue-500" },
  { icon: FolderOpen, label: "Personal", color: "bg-green-500" },
  { icon: FolderOpen, label: "Promotions", color: "bg-orange-500" },
];

export function Sidebar() {
  return (
    <aside className="hidden lg:flex w-64 flex-col border-r border-slate-800 bg-slate-950">
      {/* Quick Stats */}
      <div className="p-4">
        <div className="rounded-xl bg-gradient-to-br from-violet-600/20 to-indigo-600/20 border border-violet-500/30 p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-violet-600">
              <Mail className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="text-2xl font-bold text-white">12</p>
              <p className="text-xs text-slate-400">Unread emails</p>
            </div>
          </div>
        </div>
      </div>

      {/* Menu */}
      <nav className="flex-1 px-3 py-4">
        <div className="space-y-1">
          {menuItems.map((item, index) => (
            <motion.button
              key={item.label}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className={cn(
                "flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-sm transition-colors",
                item.active
                  ? "bg-violet-600/20 text-violet-300"
                  : "text-slate-400 hover:bg-slate-800 hover:text-white"
              )}
            >
              <div className="flex items-center gap-3">
                <item.icon className="h-4 w-4" />
                <span>{item.label}</span>
              </div>
              {item.badge > 0 && (
                <span className="rounded-full bg-violet-600 px-2 py-0.5 text-xs font-medium text-white">
                  {item.badge}
                </span>
              )}
            </motion.button>
          ))}
        </div>

        {/* Categories */}
        <div className="mt-8">
          <h3 className="px-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
            Categories
          </h3>
          <div className="mt-3 space-y-1">
            {categories.map((category, index) => (
              <motion.button
                key={category.label}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: (menuItems.length + index) * 0.05 }}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
              >
                <div className={cn("h-2 w-2 rounded-full", category.color)} />
                <span>{category.label}</span>
              </motion.button>
            ))}
          </div>
        </div>
      </nav>

      {/* Footer */}
      <div className="border-t border-slate-800 p-3">
        <div className="space-y-1">
          <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-slate-400 hover:bg-slate-800 hover:text-white transition-colors">
            <Settings className="h-4 w-4" />
            <span>Settings</span>
          </button>
          <button className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-slate-400 hover:bg-slate-800 hover:text-white transition-colors">
            <HelpCircle className="h-4 w-4" />
            <span>Help & Support</span>
          </button>
        </div>
      </div>
    </aside>
  );
}

