"use client";

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import { LoadingScreen } from "@/components/ui/loading";
import { motion } from "framer-motion";
import { CheckCircle2, XCircle, Mail } from "lucide-react";

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setToken, isAuthenticated, error } = useAuthStore();

  const token = searchParams.get("token");
  const errorParam = searchParams.get("error");

  useEffect(() => {
    if (token) {
      setToken(token);
    } else if (errorParam) {
      // Redirect to login with error
      router.push(`/login?error=${encodeURIComponent(errorParam)}`);
    }
  }, [token, errorParam, setToken, router]);

  useEffect(() => {
    if (isAuthenticated) {
      // Short delay to show success message
      const timer = setTimeout(() => {
        router.push("/dashboard");
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        router.push(`/login?error=${encodeURIComponent(error)}`);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [error, router]);

  if (error) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-red-500/20 mx-auto mb-6">
            <XCircle className="h-10 w-10 text-red-500" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Authentication Failed</h2>
          <p className="text-slate-400">{error}</p>
          <p className="text-sm text-slate-500 mt-4">Redirecting to login...</p>
        </motion.div>
      </div>
    );
  }

  if (isAuthenticated) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", duration: 0.5 }}
            className="flex h-20 w-20 items-center justify-center rounded-full bg-green-500/20 mx-auto mb-6"
          >
            <CheckCircle2 className="h-10 w-10 text-green-500" />
          </motion.div>
          <h2 className="text-2xl font-bold text-white mb-2">Welcome!</h2>
          <p className="text-slate-400">Successfully signed in</p>
          <p className="text-sm text-slate-500 mt-4">Redirecting to dashboard...</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center"
      >
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
          className="flex h-20 w-20 items-center justify-center rounded-full border-4 border-slate-800 border-t-violet-500 mx-auto mb-6"
        />
        <h2 className="text-2xl font-bold text-white mb-2">Signing you in...</h2>
        <p className="text-slate-400">Please wait while we set up your session</p>
      </motion.div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <CallbackContent />
    </Suspense>
  );
}

