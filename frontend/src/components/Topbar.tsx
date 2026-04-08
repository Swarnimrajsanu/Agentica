"use client";

import { cn } from "@/lib/cn";

export function Topbar({
  title,
  status,
}: {
  title: string;
  status: { connected: boolean; running?: boolean };
}) {
  const dot = status.connected
    ? status.running
      ? "bg-[color:var(--accent-2)]"
      : "bg-[color:var(--success)]"
    : "bg-[color:var(--danger)]";

  const label = status.connected ? (status.running ? "Running" : "Connected") : "Disconnected";

  return (
    <header className="glass sticky top-0 z-20 mx-4 mt-4 rounded-2xl px-4 py-3 md:mx-0 md:mt-0">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold tracking-wide text-white/90">{title}</div>
          <div className="text-xs text-white/50">AI-first workflows • real-time simulation</div>
        </div>
        <div className="flex items-center gap-2 rounded-xl bg-white/5 px-3 py-2 ring-1 ring-white/10">
          <span className={cn("h-2.5 w-2.5 rounded-full", dot)} />
          <span className="text-xs text-white/70">{label}</span>
        </div>
      </div>
    </header>
  );
}

