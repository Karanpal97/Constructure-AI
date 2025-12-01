"use client";

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { Mail, Sparkles, Shield, Zap, MessageSquare } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { LoginButton } from "@/components/auth/LoginButton";
import { LoadingScreen } from "@/components/ui/loading";

function LoginContent() {
  const { isAuthenticated, isLoading, error, clearError, initialize } = useAuthStore();
  const router = useRouter();
  const searchParams = useSearchParams();
  const errorParam = searchParams.get("error");

  useEffect(() => {
    initialize();
  }, [initialize]);

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return <LoadingScreen />;
  }

  const features = [
    {
      icon: Mail,
      title: "Smart Email Management",
      description: "Read, reply, and delete emails with natural language commands",
    },
    {
      icon: Sparkles,
      title: "AI-Powered Summaries",
      description: "Get instant summaries of your emails to save time",
    },
    {
      icon: MessageSquare,
      title: "Intelligent Responses",
      description: "Generate context-aware replies in seconds",
    },
    {
      icon: Zap,
      title: "Quick Actions",
      description: "Categorize, filter, and organize your inbox effortlessly",
    },
  ];

  return (
    <div className="min-h-screen animated-gradient-bg">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 h-80 w-80 rounded-full bg-violet-600/20 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 h-80 w-80 rounded-full bg-indigo-600/20 blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-96 w-96 rounded-full bg-purple-600/10 blur-3xl" />
      </div>

      <div className="relative flex min-h-screen flex-col items-center justify-center px-4 py-12">
        {/* Logo */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8 flex items-center gap-3"
        >
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-600 to-indigo-600 shadow-lg shadow-violet-500/30">
            <Mail className="h-7 w-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Constructure AI</h1>
            <p className="text-sm text-slate-400">Email Assistant</p>
          </div>
        </motion.div>

        {/* Main Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="w-full max-w-md"
        >
          <div className="glass rounded-3xl p-8 glow">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-white">Welcome Back</h2>
              <p className="mt-2 text-slate-400">
                Sign in to manage your emails with AI
              </p>
            </div>

            {/* Error Message */}
            {(error || errorParam) && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-6 rounded-xl bg-red-500/20 border border-red-500/30 px-4 py-3"
              >
                <p className="text-sm text-red-300">
                  {error || decodeURIComponent(errorParam || "An error occurred")}
                </p>
                <button
                  onClick={clearError}
                  className="mt-1 text-xs text-red-400 hover:text-red-300 underline"
                >
                  Dismiss
                </button>
              </motion.div>
            )}

            {/* Login Button */}
            <div className="mt-8 flex justify-center">
              <LoginButton />
            </div>

            {/* Security Note */}
            <div className="mt-6 flex items-center justify-center gap-2 text-xs text-slate-500">
              <Shield className="h-3.5 w-3.5" />
              <span>Secured with Google OAuth 2.0</span>
            </div>
          </div>
        </motion.div>

        {/* Features Grid */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mt-12 grid max-w-4xl grid-cols-1 gap-4 px-4 sm:grid-cols-2 lg:grid-cols-4"
        >
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 + index * 0.1 }}
              className="group rounded-2xl border border-slate-800 bg-slate-900/50 p-4 transition-all duration-300 hover:border-violet-500/50 hover:bg-slate-900/80"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600/20 to-indigo-600/20 group-hover:from-violet-600/30 group-hover:to-indigo-600/30 transition-colors">
                <feature.icon className="h-5 w-5 text-violet-400" />
              </div>
              <h3 className="mt-3 font-semibold text-white">{feature.title}</h3>
              <p className="mt-1 text-sm text-slate-400">{feature.description}</p>
            </motion.div>
          ))}
        </motion.div>

        {/* Footer */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="mt-12 text-center text-sm text-slate-500"
        >
          By signing in, you agree to our Terms of Service and Privacy Policy
        </motion.p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <LoginContent />
    </Suspense>
  );
}

