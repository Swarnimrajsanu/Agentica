"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/cn";
import type { SimulationMessage } from "@/lib/api";

function initials(name: string) {
  const parts = name.trim().split(/\s+/).slice(0, 2);
  return parts.map((p) => p[0]?.toUpperCase()).join("");
}

export function AgentMessage({
  message,
  variant = "twitter",
  highlight,
}: {
  message: SimulationMessage;
  variant?: "twitter" | "reddit";
  highlight?: boolean;
}) {
  const role = message.agent_role || "Agent";
  const isHuman = message.meta?.type === "human" || role.toLowerCase() === "human";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18 }}
      className={cn(
        "glass rounded-2xl p-3",
        highlight && "ring-2 ring-[color:var(--accent-2)]/60",
        isHuman && "ring-1 ring-[color:var(--accent)]/50",
      )}
    >
      <div className="flex items-start gap-3">
        <div
          className={cn(
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-xs font-semibold text-white/90",
            isHuman
              ? "bg-gradient-to-br from-[color:var(--accent)] to-[color:var(--accent-2)]"
              : "bg-white/8 ring-1 ring-white/10",
          )}
        >
          {initials(role) || "A"}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <div className="truncate text-xs font-semibold text-white/85">
              {role}{" "}
              <span className="ml-2 text-[10px] font-medium text-white/40">
                round {message.round}
              </span>
            </div>
            {variant === "twitter" ? (
              <span className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] text-white/50 ring-1 ring-white/10">
                post
              </span>
            ) : null}
          </div>
          <div className="mt-1 text-sm leading-relaxed text-white/80">{message.content}</div>
        </div>
      </div>
    </motion.div>
  );
}

