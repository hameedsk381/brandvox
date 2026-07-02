import React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "outline" | "success" | "warning" | "destructive";
}

export const Badge = ({ className, variant = "default", ...props }: BadgeProps) => {
  const baseStyles = "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2";
  
  const variants = {
    default: "border-transparent bg-primary text-primary-foreground hover:brightness-110",
    secondary: "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
    outline: "text-foreground border-border bg-transparent",
    success: "border-transparent bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    warning: "border-transparent bg-amber-500/10 text-amber-400 border-amber-500/20",
    destructive: "border-transparent bg-rose-500/10 text-rose-400 border-rose-500/20",
  };

  return (
    <div className={cn(baseStyles, variants[variant], className)} {...props} />
  );
};
