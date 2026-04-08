"use client";

import * as React from "react";
import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

export function Button({
  className,
  variant = "primary",
  size = "md",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
}) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-xl font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--accent-2)] disabled:opacity-50 disabled:pointer-events-none";

  const variants: Record<Variant, string> = {
    primary:
      "bg-gradient-to-r from-[color:var(--accent)] to-[color:var(--accent-2)] text-white shadow-[0_10px_30px_rgba(47,123,255,0.18)] hover:opacity-95",
    secondary:
      "glass text-[color:var(--foreground)] hover:bg-white/10",
    ghost:
      "bg-transparent text-[color:var(--foreground)] hover:bg-white/5",
    danger:
      "bg-[color:var(--danger)]/90 text-white hover:bg-[color:var(--danger)]",
  };

  const sizes: Record<Size, string> = {
    sm: "h-9 px-3 text-sm",
    md: "h-10 px-4 text-sm",
    lg: "h-11 px-5 text-base",
  };

  return <button className={cn(base, variants[variant], sizes[size], className)} {...props} />;
}

