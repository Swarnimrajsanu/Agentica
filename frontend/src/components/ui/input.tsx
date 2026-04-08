"use client";

import * as React from "react";
import { cn } from "@/lib/cn";

export function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-10 w-full rounded-xl bg-white/5 px-3 text-sm text-white/90 outline-none ring-1 ring-white/10 placeholder:text-white/40 focus:ring-2 focus:ring-[color:var(--accent-2)]",
        className,
      )}
      {...props}
    />
  );
}

