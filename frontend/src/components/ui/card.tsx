"use client";

import { forwardRef, HTMLAttributes, ReactNode } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface CardProps {
  variant?: "default" | "glass" | "gradient";
  children?: ReactNode;
  className?: string;
}

const variantStyles = {
  default: "bg-slate-900/80 border border-slate-800",
  glass: "bg-slate-900/40 backdrop-blur-xl border border-slate-700/50",
  gradient: "bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 border border-slate-700/50",
};

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = "default", children }, ref) => {
    return (
      <motion.div
        ref={ref}
        className={cn(
          "rounded-2xl p-6 shadow-xl",
          variantStyles[variant],
          className
        )}
      >
        {children}
      </motion.div>
    );
  }
);

Card.displayName = "Card";

export const CardHeader = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 pb-4", className)}
    {...props}
  />
));

CardHeader.displayName = "CardHeader";

export const CardTitle = forwardRef<
  HTMLHeadingElement,
  HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn("text-xl font-semibold text-white", className)}
    {...props}
  />
));

CardTitle.displayName = "CardTitle";

export const CardContent = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("", className)} {...props} />
));

CardContent.displayName = "CardContent";

