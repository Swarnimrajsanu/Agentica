"use client";

import { useMemo, useState } from "react";
import { Topbar } from "@/components/Topbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

type ChatMsg = { role: "user" | "agent"; content: string; at: number };

const agentOptions = ["Customer", "Investor", "Expert", "Marketing", "Critic", "Red Team"];

export default function AgentChatPage() {
  const [agent, setAgent] = useState(agentOptions[0]);
  const [text, setText] = useState("");
  const [messages, setMessages] = useState<ChatMsg[]>([]);

  const transcript = useMemo(() => messages, [messages]);

  function send() {
    const t = text.trim();
    if (!t) return;
    setMessages((prev) => [...prev, { role: "user", content: t, at: Date.now() }]);
    setText("");

    // Optional backend integration point:
    // Add a FastAPI endpoint to chat with a single agent; for now we keep this UI-only.
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { role: "agent", content: `(${agent}) I hear you. If you want this wired up, expose an agent-chat endpoint.`, at: Date.now() },
      ]);
    }, 420);
  }

  return (
    <div className="px-4 md:px-0">
      <Topbar title="Agent Chat" status={{ connected: true, running: false }} />
      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Settings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="text-xs text-white/60">Select agent</div>
            <select
              className="h-10 w-full rounded-xl bg-white/5 px-3 text-sm text-white/90 ring-1 ring-white/10 outline-none focus:ring-2 focus:ring-[color:var(--accent-2)]"
              value={agent}
              onChange={(e) => setAgent(e.target.value)}
            >
              {agentOptions.map((a) => (
                <option key={a} value={a} className="bg-[#0b0f1a]">
                  {a}
                </option>
              ))}
            </select>
            <div className="text-xs text-white/55">
              This page is ready for wiring to backend when you add a dedicated agent chat API.
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Conversation</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="max-h-[460px] space-y-2 overflow-auto rounded-2xl bg-black/20 p-2 ring-1 ring-white/10">
              {transcript.map((m) => (
                <div
                  key={m.at}
                  className={
                    m.role === "user"
                      ? "ml-auto max-w-[85%] rounded-2xl bg-white/8 p-3 text-sm text-white/85 ring-1 ring-white/10"
                      : "mr-auto max-w-[85%] rounded-2xl bg-gradient-to-br from-white/6 to-white/3 p-3 text-sm text-white/80 ring-1 ring-white/10"
                  }
                >
                  <div className="mb-1 text-[10px] uppercase tracking-wide text-white/45">
                    {m.role === "user" ? "You" : agent}
                  </div>
                  {m.content}
                </div>
              ))}
              {!transcript.length ? <div className="p-3 text-sm text-white/55">Start a chat.</div> : null}
            </div>

            <div className="mt-3 grid gap-2">
              <Textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Ask the agent..." className="min-h-20" />
              <div className="flex gap-2">
                <Button onClick={send}>Send</Button>
                <Input
                  value={agent}
                  onChange={(e) => setAgent(e.target.value)}
                  placeholder="Agent name"
                  className="hidden"
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

