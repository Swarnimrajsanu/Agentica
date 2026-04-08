"use client";

import type { SimulationMessage } from "@/lib/api";
import { AgentMessage } from "@/components/AgentMessage";

export function RedditThread({
  round,
  messages,
}: {
  round: number;
  messages: SimulationMessage[];
}) {
  return (
    <div className="glass rounded-2xl p-3">
      <div className="mb-3 text-xs font-semibold tracking-wide text-white/70">Round {round}</div>
      <div className="space-y-2">
        {messages.map((m, idx) => (
          <div key={`${m.agent_role}-${idx}`} className="pl-2 border-l border-white/10">
            <AgentMessage message={m} variant="reddit" />
          </div>
        ))}
      </div>
    </div>
  );
}

