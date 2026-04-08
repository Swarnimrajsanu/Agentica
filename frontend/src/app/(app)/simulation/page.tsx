"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Topbar } from "@/components/Topbar";
import { AgentMessage } from "@/components/AgentMessage";
import { RedditThread } from "@/components/RedditThread";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useSimulationSocket } from "@/hooks/useSimulationSocket";

export default function SimulationPage() {
  const params = useSearchParams();
  const topic = params.get("topic") || "Should we launch an AI note-taking app?";

  const socket = useSimulationSocket(topic);
  const [humanMessage, setHumanMessage] = useState("");
  const [humanName, setHumanName] = useState("Human");
  const [influence, setInfluence] = useState(0.6);

  const feedRef = useRef<HTMLDivElement | null>(null);

  const byRound = useMemo(() => {
    const map = new Map<number, typeof socket.messages>();
    for (const m of socket.messages) {
      const arr = map.get(m.round) || [];
      arr.push(m);
      map.set(m.round, arr);
    }
    return [...map.entries()].sort((a, b) => a[0] - b[0]);
  }, [socket]);

  const twitterMessages = socket.messages;
  const redditThreads = byRound;

  function injectHuman() {
    const msg = humanMessage.trim();
    if (!msg) return;
    socket.sendHumanMessage({ message: msg, influence_level: influence, display_name: humanName });
    setHumanMessage("");
  }

  useEffect(() => {
    const el = feedRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [socket.messages.length]);

  return (
    <div className="px-4 md:px-0">
      <Topbar title="Simulation (real-time)" status={{ connected: socket.connected, running: socket.running }} />

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card className="min-h-[620px]">
          <CardHeader>
            <CardTitle>Twitter-sim</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="mb-3 text-xs text-white/55">
              Topic: <span className="text-white/80">{topic}</span>
            </div>
            <div
              ref={feedRef}
              className="max-h-[480px] space-y-2 overflow-auto rounded-2xl bg-black/20 p-2 ring-1 ring-white/10"
            >
              {twitterMessages.map((m, idx) => (
                <AgentMessage
                  key={`${m.agent_role}-${m.round}-${idx}`}
                  message={m}
                  highlight={m.meta?.type === "human"}
                />
              ))}
              {!twitterMessages.length ? (
                <div className="p-4 text-sm text-white/55">
                  {socket.connected ? "Agents thinking..." : "Connecting..."}
                </div>
              ) : null}
            </div>

            <div className="mt-3 glass rounded-2xl p-3">
              <div className="mb-2 text-xs font-semibold text-white/70">Human as an Agent</div>
              <div className="grid gap-2 md:grid-cols-3">
                <Input value={humanName} onChange={(e) => setHumanName(e.target.value)} placeholder="Your name" />
                <Input
                  type="number"
                  min={0.1}
                  max={1}
                  step={0.1}
                  value={influence}
                  onChange={(e) => setInfluence(Number(e.target.value))}
                  placeholder="Influence (0.1-1.0)"
                />
                <div className="flex gap-2">
                  <Button onClick={injectHuman} className="flex-1">
                    Post argument
                  </Button>
                  <Button variant="ghost" onClick={socket.close}>
                    Stop
                  </Button>
                </div>
              </div>
              <div className="mt-2">
                <Textarea
                  value={humanMessage}
                  onChange={(e) => setHumanMessage(e.target.value)}
                  placeholder="Post your argument alongside AI agents..."
                  className="min-h-20"
                />
              </div>
              {socket.predictionUpdate ? (
                <div className="mt-2 text-xs text-white/55">
                  Prediction updated after round {socket.predictionUpdate.round}.
                </div>
              ) : null}
              {socket.error ? <div className="mt-2 text-xs text-(--danger)">{socket.error}</div> : null}
            </div>
          </CardContent>
        </Card>

        <Card className="min-h-[620px]">
          <CardHeader>
            <CardTitle>Reddit-sim</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="max-h-[560px] space-y-3 overflow-auto rounded-2xl bg-black/20 p-2 ring-1 ring-white/10">
              {redditThreads.map(([r, msgs]) => (
                <RedditThread key={r} round={r} messages={msgs} />
              ))}
              {!redditThreads.length ? (
                <div className="p-4 text-sm text-white/55">Waiting for threads...</div>
              ) : null}
            </div>
          </CardContent>
        </Card>
      </div>

      {socket.predictionUpdate ? (
        <div className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Live prediction update</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="max-h-[320px] overflow-auto rounded-2xl bg-black/30 p-3 text-xs text-white/75 ring-1 ring-white/10">
                {JSON.stringify(socket.predictionUpdate.prediction, null, 2)}
              </pre>
            </CardContent>
          </Card>
        </div>
      ) : null}
    </div>
  );
}

