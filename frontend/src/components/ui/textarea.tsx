"use client";

import * as React from "react";
import { cn } from "@/lib/cn";

export function Textarea({
  className,
  ...props
}: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        "min-h-28 w-full resize-none rounded-2xl bg-white/5 p-3 text-sm text-white/90 outline-none ring-1 ring-white/10 placeholder:text-white/40 focus:ring-2 focus:ring-[color:var(--accent-2)]",
        className,
      )}
      {...props}
    />
  );
}

