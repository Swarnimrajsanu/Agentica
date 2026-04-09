"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useRouter } from "next/navigation";
import { Topbar } from "@/components/Topbar";
import { AgentMessage } from "@/components/AgentMessage";
import { RedditThread } from "@/components/RedditThread";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useSimulationSocket } from "@/hooks/useSimulationSocket";
import { motion } from "framer-motion";
import { cn } from "@/lib/cn";
import { RelationshipGraph } from "@/components/RelationshipGraph";
import { RedTeamReport } from "@/components/RedTeamReport";
import { Trash2, ShieldAlert } from "lucide-react";

type Stance = "support" | "oppose" | "neutral";

function stanceFromText(text: string): Stance {
  const t = text.toLowerCase();
  const supportHints = ["yes", "should", "go", "proceed", "recommend", "strong go", "launch", "bullish", "upside"];
  const opposeHints = ["no", "don't", "do not", "avoid", "risk", "fail", "no-go", "fatal", "bearish", "concern"];
  const s = supportHints.some((k) => t.includes(k));
  const o = opposeHints.some((k) => t.includes(k));
  if (s && !o) return "support";
  if (o && !s) return "oppose";
  return "neutral";
}

function stanceColor(stance: Stance) {
  if (stance === "support") return { dot: "bg-(--success)", border: "border-l-(--success)", badge: "bg-(--success)/15 text-white/80 ring-1 ring-(--success)/30" };
  if (stance === "oppose") return { dot: "bg-(--danger)", border: "border-l-(--danger)", badge: "bg-(--danger)/15 text-white/80 ring-1 ring-(--danger)/30" };
  return { dot: "bg-amber-400", border: "border-l-amber-400", badge: "bg-amber-400/15 text-white/80 ring-1 ring-amber-400/30" };
}

function clamp01(n: number) {
  return Math.max(0, Math.min(1, n));
}

function formatMs(ms: number) {
  const s = Math.floor(ms / 1000);
  const mm = Math.floor(s / 60);
  const ss = s % 60;
  return `${mm}:${String(ss).padStart(2, "0")}`;
}

function ConfidenceGauge({ value }: { value: number }) {
  const v = Math.max(0, Math.min(100, value));
  const r = 44;
  const c = 2 * Math.PI * r;
  const dash = (v / 100) * c;
  const angle = (-90 + (v / 100) * 180) * (Math.PI / 180);
  const needleX = 52 + Math.cos(angle) * 34;
  const needleY = 56 + Math.sin(angle) * 34;

  return (
    <div className="flex items-center justify-between gap-4">
      <div>
        <div className="text-xs font-semibold tracking-wide text-white/70">Confidence</div>
        <div className="mt-1 text-2xl font-semibold text-white/90">{Math.round(v)}%</div>
        <div className="mt-1 text-xs text-white/45">updates as prediction changes</div>
      </div>
      <div className="relative h-[112px] w-[120px]">
        <svg viewBox="0 0 120 80" className="h-full w-full">
          <path d="M16 64 A44 44 0 0 1 104 64" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="10" strokeLinecap="round" />
          <path
            d="M16 64 A44 44 0 0 1 104 64"
            fill="none"
            stroke="url(#g)"
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={`${dash} ${c}`}
          />
          <defs>
            <linearGradient id="g" x1="0" x2="1">
              <stop offset="0%" stopColor="rgba(109,94,252,0.95)" />
              <stop offset="100%" stopColor="rgba(47,123,255,0.95)" />
            </linearGradient>
          </defs>
          <motion.line
            x1="52"
            y1="56"
            x2={needleX}
            y2={needleY}
            stroke="rgba(255,255,255,0.82)"
            strokeWidth="2"
            initial={false}
            animate={{ x2: needleX, y2: needleY }}
            transition={{ type: "spring", stiffness: 120, damping: 14 }}
          />
          <circle cx="52" cy="56" r="3" fill="rgba(255,255,255,0.9)" />
        </svg>
      </div>
    </div>
  );
}

function MiniHeatmap({
  agents,
  matrix,
}: {
  agents: string[];
  matrix: number[][];
}) {
  const n = Math.min(6, agents.length);
  const grid = Array.from({ length: n }, (_, i) =>
    Array.from({ length: n }, (_, j) => matrix[i]?.[j] ?? 0),
  );

  function cellColor(v: number) {
    // v in [0,1] => red -> yellow -> green
    if (v >= 0.66) return "bg-(--success)/70";
    if (v >= 0.33) return "bg-amber-400/60";
    return "bg-(--danger)/60";
  }

  return (
    <div>
      <div className="mb-2 text-xs font-semibold tracking-wide text-white/70">Mini Consensus Heatmap</div>
      <div className="grid grid-cols-6 gap-1">
        {grid.flatMap((row, i) =>
          row.map((v, j) => (
            <div
              key={`${i}-${j}`}
              className={cn("h-5 w-5 rounded-md ring-1 ring-white/10", cellColor(v))}
              title={`${agents[i] ?? ""} ↔ ${agents[j] ?? ""}: ${(v * 100).toFixed(1)}%`}
            />
          )),
        )}
      </div>
      <div className="mt-2 text-[10px] text-white/45">Green=agree • Red=disagree • Yellow=partial</div>
    </div>
  );
}

function StanceDistribution({ support, oppose, neutral }: { support: number; oppose: number; neutral: number }) {
  const total = Math.max(1, support + oppose + neutral);
  const s = (support / total) * 100;
  const o = (oppose / total) * 100;
  const n = (neutral / total) * 100;

  return (
    <div>
      <div className="mb-2 text-xs font-semibold tracking-wide text-white/70">Stance Distribution</div>
      <div className="h-3 w-full overflow-hidden rounded-full bg-white/6 ring-1 ring-white/10">
        <div className="flex h-full w-full">
          <div className="h-full bg-(--success)/70" style={{ width: `${s}%` }} />
          <div className="h-full bg-(--danger)/70" style={{ width: `${o}%` }} />
          <div className="h-full bg-amber-400/70" style={{ width: `${n}%` }} />
        </div>
      </div>
      <div className="mt-2 flex items-center justify-between text-[11px] text-white/55">
        <span>Support: {Math.round(s)}%</span>
        <span>Oppose: {Math.round(o)}%</span>
        <span>Neutral: {Math.round(n)}%</span>
      </div>
    </div>
  );
}

export default function SimulationPage() {
  const params = useSearchParams();
  const router = useRouter();
  const topic = params.get("topic") || "Should we launch an AI note-taking app?";

  const socket = useSimulationSocket(topic);
  const [tab, setTab] = useState<"twitter" | "reddit" | "graph" | "redteam" | "prediction">("twitter");
  const [allSims, setAllSims] = useState<any[]>([]);

  // Auto-switch to prediction when done
  useEffect(() => {
    if (socket.completed) {
        setTab("prediction");
    }
  }, [socket.completed]);

  // Fetch all simulations (active + history)
  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE || "https://crispy-umbrella-97774w549xvqfxgj-8000.app.github.dev/api";
    Promise.all([
        fetch(`${apiBase}/simulate/active`).then(res => {
          if (!res.ok) throw new Error(`Active fetch failed: ${res.status}`);
          return res.json();
        }),
        fetch(`${apiBase}/simulate/history`).then(res => {
          if (!res.ok) throw new Error(`History fetch failed: ${res.status}`);
          return res.json();
        })
    ]).then(([activeData, historyData]) => {
        const active = activeData.active_simulations || [];
        const history = historyData.history || [];
        
        // combine and uniquify by ID
        const combined = [...active];
        history.forEach((h: any) => {
            if (!combined.find(s => s.id === h.simulation_id || s.simulation_id === h.simulation_id)) {
                combined.push(h);
            }
        });
        setAllSims(combined);
    }).catch(err => {
      console.error("Failed to fetch simulations:", err);
      // Optionally set empty state or show error message
      setAllSims([]);
    });
  }, [topic]);

  const handleDelete = async (e: React.MouseEvent, simId: string) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this simulation?")) return;
    
    const apiBase = process.env.NEXT_PUBLIC_API_BASE || "https://crispy-umbrella-97774w549xvqfxgj-8000.app.github.dev/api";
    try {
        await fetch(`${apiBase}/simulate/${simId}`, { method: 'DELETE' });
        setAllSims(prev => prev.filter(s => (s.id || s.simulation_id) !== simId));
    } catch (err) {
        console.error("Delete failed", err);
    }
  };

  const handleClearAll = async () => {
    if (!confirm("Are you sure you want to clear ALL simulation history? This cannot be undone.")) return;
    
    const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api";
    try {
        await fetch(`${apiBase}/simulate/history/clear-all`, { method: 'DELETE' });
        setAllSims([]);
    } catch (err) {
        console.error("Clear failed", err);
    }
  };

  const [humanMessage, setHumanMessage] = useState("");
  const [humanName, setHumanName] = useState("Human");
  const [influence, setInfluence] = useState(0.6);

  const feedRef = useRef<HTMLDivElement | null>(null);
  const startAtRef = useRef<number | null>(null);
  const [elapsed, setElapsed] = useState(0);

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

  useEffect(() => {
    if (socket.running) {
      if (!startAtRef.current) startAtRef.current = Date.now();
    } else {
      startAtRef.current = null;
    }
  }, [socket.running]);

  useEffect(() => {
    const simId = socket.completed?.simulation_id;
    if (!simId) return;
    // Redirect to the final prediction report for this simulation.
    router.push(
      `/predictions?simulation_id=${encodeURIComponent(simId)}&topic=${encodeURIComponent(topic)}`,
    );
  }, [socket.completed?.simulation_id, router, topic]);

  useEffect(() => {
    if (!socket.running) return;
    const id = window.setInterval(() => {
      if (!startAtRef.current) return;
      setElapsed(Date.now() - startAtRef.current);
    }, 250);
    return () => window.clearInterval(id);
  }, [socket.running]);

  const agentRoster = useMemo(() => {
    const base = [
      { emoji: "🧑‍💼", name: "Customer", role: "market-fit lens", personality: "cautious", influenceScore: 0.56 },
      { emoji: "💰", name: "Investor", role: "ROI + moat lens", personality: "analytical", influenceScore: 0.62 },
      { emoji: "🔬", name: "Expert", role: "technical validity", personality: "data-driven", influenceScore: 0.68 },
      { emoji: "📢", name: "Marketing", role: "positioning + growth", personality: "creative", influenceScore: 0.58 },
      { emoji: "⚖️", name: "Critic", role: "assumption checking", personality: "contrarian", influenceScore: 0.60 },
      { emoji: "🔴", name: "Red Team", role: "adversarial pressure", personality: "adversarial", influenceScore: 0.72 },
    ];

    // Update stance based on latest message per agent
    const latest: Record<string, string> = {};
    for (const m of socket.messages) latest[m.agent_role] = m.content;

    return base.map((a) => {
      const text = latest[a.name] ?? "";
      const stance = text ? stanceFromText(text) : "neutral";
      return { ...a, stance };
    });
  }, [socket.messages]);

  const distribution = useMemo(() => {
    let support = 0;
    let oppose = 0;
    let neutral = 0;
    for (const a of agentRoster) {
      if (a.stance === "support") support += 1;
      else if (a.stance === "oppose") oppose += 1;
      else neutral += 1;
    }
    return { support, oppose, neutral };
  }, [agentRoster]);

  const opinionShifts = useMemo(() => {
    const seen = new Map<string, Stance>();
    const shifted = new Set<string>();
    for (const m of socket.messages) {
      const st = stanceFromText(m.content);
      const prev = seen.get(m.agent_role);
      if (prev && prev !== st) shifted.add(m.agent_role);
      seen.set(m.agent_role, st);
    }
    return shifted.size;
  }, [socket.messages]);

  const strongestArgument = useMemo(() => {
    if (!socket.messages.length) return "—";
    const best = [...socket.messages].sort((a, b) => (b.content?.length ?? 0) - (a.content?.length ?? 0))[0];
    const snippet = (best.content || "").slice(0, 80).trim();
    return `${best.agent_role}: ${snippet}${best.content.length > 80 ? "…" : ""}`;
  }, [socket.messages]);

  const confidence = useMemo(() => {
    const p = socket.predictionUpdate?.prediction as
      | { confidence_level?: unknown; weighted_consensus?: { weighted_agreement_level?: unknown } }
      | undefined;
    const c = p?.confidence_level;
    if (typeof c === "number") return c;
    // fallback: infer from weighted consensus if present
    const wc = p?.weighted_consensus?.weighted_agreement_level;
    if (typeof wc === "number") return wc;
    return 50;
  }, [socket.predictionUpdate]);

  const round = socket.round ?? 0;
  const totalRounds = 3;
  const progress = clamp01(totalRounds ? round / totalRounds : 0);

  return (
    <div className="px-4 md:px-0">
      <Topbar title="Simulation (real-time)" status={{ connected: socket.connected, running: socket.running }} />

      <div className="mt-4 grid gap-4 lg:grid-cols-12">
        {/* LEFT: Active Agents + Simulations */}
        <div className="lg:col-span-3 space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle>Simulation History</CardTitle>
              {allSims.length > 0 && (
                  <button 
                    onClick={handleClearAll}
                    className="text-[10px] text-red-500/50 hover:text-red-500 transition px-2 py-1 rounded hover:bg-red-500/5"
                  >
                    Clear All
                  </button>
              )}
            </CardHeader>
            <CardContent className="space-y-2">
              {allSims.length === 0 ? (
                <div className="text-xs text-white/40 p-2">No historical simulations found.</div>
              ) : (
                allSims.map((sim) => (
                  <div key={sim.id || sim.simulation_id} className="group relative">
                    <button
                        onClick={() => router.push(`/simulation?topic=${encodeURIComponent(sim.topic)}`)}
                        className={cn(
                            "w-full text-left p-2 rounded-xl text-[11px] transition glass border border-white/5 hover:border-white/20",
                            topic === sim.topic ? "ring-1 ring-(--accent-2)" : ""
                        )}
                    >
                        <div className="font-semibold text-white/80 truncate pr-6">{sim.topic}</div>
                        <div className="text-white/40 mt-0.5 flex justify-between">
                            <span>Round {sim.round || sim.messages?.length || 0}</span>
                            <span className="capitalize">{sim.status}</span>
                        </div>
                    </button>
                    <button
                        onClick={(e) => handleDelete(e, sim.id || sim.simulation_id)}
                        className="absolute top-2 right-2 p-1 rounded-md text-white/20 hover:text-white/80 hover:bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Delete simulation"
                    >
                        <Trash2 size={12} />
                    </button>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card>
          <CardHeader>
            <CardTitle>Active Agents</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {agentRoster.map((a) => {
              const sc = stanceColor(a.stance);
              return (
                <div key={a.name} className="glass rounded-2xl p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/6 text-lg ring-1 ring-white/10">
                        {a.emoji}
                      </div>
                      <div className="min-w-0">
                        <div className="truncate text-sm font-semibold text-white/90">
                          {a.name}{" "}
                          <span className="ml-2 text-[10px] font-medium text-white/45">{a.role}</span>
                        </div>
                        <div className="mt-1 flex items-center gap-2">
                          <span className="rounded-full bg-white/6 px-2 py-0.5 text-[10px] text-white/60 ring-1 ring-white/10">
                            {a.personality}
                          </span>
                          <span className="flex items-center gap-1 text-[10px] text-white/55">
                            <span className={cn("h-2 w-2 rounded-full", sc.dot)} />
                            {a.stance}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="mt-3">
                    <div className="mb-1 flex items-center justify-between text-[10px] text-white/45">
                      <span>Influence</span>
                      <span>{a.influenceScore.toFixed(2)}</span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-white/6 ring-1 ring-white/10">
                      <div
                        className="h-full bg-linear-to-r from-(--accent) to-(--accent-2)"
                        style={{ width: `${Math.round(a.influenceScore * 100)}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}

            <Button variant="secondary" className="w-full">
              <span className="mr-1">👤</span> Join as Agent
            </Button>
          </CardContent>
        </Card>
        </div>

        {/* CENTER: Simulation Feed */}
        <Card className="lg:col-span-6">
          <CardHeader>
            <CardTitle>Simulation Feed</CardTitle>
          </CardHeader>
          <CardContent>
            {/* top status bar */}
            <div className="glass rounded-2xl p-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="text-sm text-white/80">
                  <span className="font-semibold text-white/90">Round {round}</span>{" "}
                  <span className="text-white/50">of {totalRounds}</span>
                </div>
                <div className="text-xs text-white/55">elapsed: {formatMs(elapsed)}</div>
              </div>
              <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-white/6 ring-1 ring-white/10">
                <motion.div
                  className="h-full bg-linear-to-r from-(--accent) to-(--accent-2)"
                  initial={false}
                  animate={{ width: `${Math.round(progress * 100)}%` }}
                  transition={{ type: "spring", stiffness: 120, damping: 18 }}
                />
              </div>
            </div>

            {/* tabs */}
            <div className="mt-3 grid grid-cols-2 gap-2">
              <button
                className={cn(
                  "glass rounded-2xl px-3 py-2 text-sm font-semibold text-white/70 transition",
                  tab === "twitter" && "ring-2 ring-(--accent-2)/50 text-white",
                )}
                onClick={() => setTab("twitter")}
              >
                Twitter-Sim
              </button>
              <button
                className={cn(
                  "glass rounded-2xl px-3 py-2 text-sm font-semibold text-white/70 transition",
                  tab === "reddit" && "ring-2 ring-(--accent-2)/50 text-white",
                )}
                onClick={() => setTab("reddit")}
              >
                Reddit-Sim
              </button>
              <button
                className={cn(
                  "glass rounded-2xl px-3 py-2 text-sm font-semibold text-white/70 transition col-span-2",
                  tab === "graph" && "ring-2 ring-(--accent-2)/50 text-white",
                )}
                onClick={() => setTab("graph")}
              >
                Live Graph
              </button>
              <button
                className={cn(
                  "glass rounded-2xl px-3 py-2 text-sm font-semibold text-white/70 transition flex items-center justify-center gap-2",
                  tab === "redteam" && "ring-2 ring-red-500/50 text-red-400 bg-red-500/10",
                )}
                onClick={() => setTab("redteam")}
              >
                <ShieldAlert size={14} /> Red Team
              </button>
              <button
                className={cn(
                  "glass rounded-2xl px-3 py-2 text-sm font-semibold text-white/70 transition",
                  tab === "prediction" && "ring-2 ring-purple-500/50 text-purple-400 bg-purple-500/10",
                )}
                onClick={() => setTab("prediction")}
              >
                Prediction
              </button>
            </div>

            {/* feed */}
            <div
              ref={feedRef}
              className="mt-3 max-h-[520px] space-y-2 overflow-auto rounded-2xl bg-black/20 p-2 ring-1 ring-white/10 scroll-smooth"
            >
              {tab === "twitter" && twitterMessages.map((m, idx) => {
                  const st = stanceFromText(m.content);
                  const sc = stanceColor(st);
                  return (
                    <motion.div
                      key={`${m.agent_role}-${m.round}-${idx}`}
                      initial={{ opacity: 0, x: -12 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.18 }}
                      className={cn("border-l-4 pl-2", sc.border)}
                    >
                      <div className="mb-1 flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2 text-xs text-white/70">
                          <span className="text-sm">{agentRoster.find((a) => a.name === m.agent_role)?.emoji ?? "💬"}</span>
                          <span className="font-semibold text-white/85">{m.agent_role}</span>
                          <span className="text-white/35">•</span>
                          <span className="text-[10px] text-white/50">{m.timestamp ? new Date(m.timestamp).toLocaleTimeString() : "now"}</span>
                        </div>
                        <span className={cn("rounded-full px-2 py-0.5 text-[10px]", sc.badge)}>{st}</span>
                      </div>
                      <AgentMessage message={m} highlight={m.meta?.type === "human"} />
                      <div className="mt-2 flex gap-2">
                        <button className="rounded-xl bg-white/5 px-3 py-1 text-xs text-white/60 ring-1 ring-white/10 hover:bg-white/8">
                          👍 Like
                        </button>
                        <button className="rounded-xl bg-white/5 px-3 py-1 text-xs text-white/60 ring-1 ring-white/10 hover:bg-white/8">
                          👎 Disagree
                        </button>
                      </div>
                    </motion.div>
                  );
                })}

              {tab === "reddit" && (
                <div className="space-y-3">
                  {redditThreads.map(([r, msgs]) => (
                    <div key={r} className="rounded-2xl">
                      <RedditThread round={r} messages={msgs} />
                    </div>
                  ))}
                </div>
              )}

              {tab === "graph" && (
                <div className="h-[480px] w-full">
                    <RelationshipGraph messages={socket.messages} graphData={socket.graphData} />
                </div>
              )}

              {tab === "redteam" && (
                <div className="h-[480px] w-full overflow-auto pr-2 custom-scrollbar">
                    <RedTeamReport data={socket.redTeamData} />
                </div>
              )}

              {tab === "prediction" && (
                <div className="h-[480px] w-full overflow-auto pr-2 custom-scrollbar space-y-6 p-2">
                    {socket.predictionUpdate ? (
                        <div className="space-y-6">
                            <div className="glass rounded-3xl p-6 border border-purple-500/20 bg-gradient-to-br from-purple-500/5 to-transparent text-center">
                                <div className="text-[10px] text-purple-400 uppercase tracking-[0.2em] mb-2 font-bold">Final Consensus Projection</div>
                                <h1 className="text-2xl font-bold text-white/90 leading-tight">{(socket.predictionUpdate.prediction as any)?.final_decision || "No prediction yet"}</h1>
                                <div className="mt-4 flex items-center justify-center gap-6">
                                    <div className="text-center">
                                        <div className="text-2xl font-mono font-bold text-purple-400">{(socket.predictionUpdate.prediction as any)?.confidence}%</div>
                                        <div className="text-[9px] text-white/30 uppercase tracking-widest">Confidence</div>
                                    </div>
                                    <div className="h-8 w-px bg-white/10" />
                                    <div className="text-center">
                                        <div className="text-2xl font-mono font-bold text-blue-400">{(socket.predictionUpdate.prediction as any)?.key_reasoning?.length || 0}</div>
                                        <div className="text-[9px] text-white/30 uppercase tracking-widest">Core Proofs</div>
                                    </div>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="glass rounded-2xl p-4 border border-white/5 space-y-3">
                                    <h3 className="text-[11px] font-bold text-white/30 uppercase tracking-widest">Key Reasoning</h3>
                                    <ul className="space-y-2">
                                        {((socket.predictionUpdate.prediction as any)?.key_reasoning || []).map((r: string, i: number) => (
                                            <li key={i} className="text-xs text-white/70 leading-relaxed flex gap-2">
                                                <span className="text-purple-500/50">•</span> {r}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                                <div className="glass rounded-2xl p-4 border border-white/5 space-y-3">
                                    <h3 className="text-[11px] font-bold text-white/30 uppercase tracking-widest text-orange-400/60">Identified Risks</h3>
                                    <ul className="space-y-2">
                                        {((socket.predictionUpdate.prediction as any)?.risks || []).map((r: string, i: number) => (
                                            <li key={i} className="text-xs text-white/70 leading-relaxed flex gap-2">
                                                <span className="text-orange-500/50">•</span> {r}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </div>

                            <div className="glass rounded-2xl p-5 border border-white/5 bg-white/5 italic text-sm text-white/60 leading-relaxed text-center">
                                "{(socket.predictionUpdate.consensus as any)?.consensus || "Synthesis pending..."}"
                            </div>

                            {/* Red Team Integration into Prediction */}
                            {socket.redTeamData && (
                                <div className="space-y-4">
                                    <div className="flex items-center gap-2 px-2">
                                        <ShieldAlert size={14} className="text-red-500" />
                                        <h3 className="text-[11px] font-bold text-red-500 uppercase tracking-widest">Adversarial Counter-Analysis</h3>
                                    </div>
                                    <div className="glass rounded-2xl p-5 border border-red-500/20 bg-red-500/5 relative overflow-hidden">
                                        <div className="absolute top-0 right-0 p-4 opacity-10">
                                            <ShieldAlert size={64} />
                                        </div>
                                        <div className="flex items-center justify-between mb-4">
                                            <div className="text-xs text-white/50 italic">"The agents may be suffering from groupthink. Red Team has found significant blind spots in the proposed decision."</div>
                                            <div className="text-right">
                                                <div className="text-xl font-mono font-bold text-red-400">{socket.redTeamData.revised_confidence}%</div>
                                                <div className="text-[9px] text-white/30 uppercase tracking-widest leading-none">Adjusted Conf.</div>
                                            </div>
                                        </div>
                                        <div className="space-y-3">
                                            {(socket.redTeamData.vulnerabilities || []).slice(0, 2).map((v: any, i: number) => (
                                                <div key={i} className="flex gap-3 items-start border-l-2 border-red-500/30 pl-3">
                                                    <div>
                                                        <div className="text-[10px] font-bold text-red-400">{v.level} — {v.name}</div>
                                                        <div className="text-[10px] text-white/60 leading-relaxed">{v.description}</div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                        <div className="mt-4 pt-4 border-t border-white/5 text-center">
                                            <button 
                                                onClick={() => setTab("redteam")}
                                                className="text-[10px] text-red-400/80 hover:text-red-400 underline decoration-red-400/30 underline-offset-4"
                                            >
                                                View Full Adversarial Report
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-white/30 space-y-4">
                            <div className="animate-pulse h-12 w-12 rounded-full border-2 border-purple-500/20 flex items-center justify-center">
                                <div className="h-6 w-6 rounded-full border-2 border-purple-500/40 border-t-purple-500 animate-spin" />
                            </div>
                            <p className="text-xs font-mono uppercase tracking-widest">Synthesizing Final Prediction...</p>
                        </div>
                    )}
                </div>
              )}

              {!socket.messages.length ? (
                <div className="p-4 text-sm text-white/55">{socket.connected ? "Agents thinking..." : "Connecting..."}</div>
              ) : null}
            </div>

            {/* human input */}
            <div className="mt-3 glass rounded-2xl p-3">
              <div className="mb-2 flex items-center justify-between gap-3">
                <div className="text-xs font-semibold text-white/70">Type your argument…</div>
                <div className="text-[10px] text-white/45">Human-as-an-Agent</div>
              </div>
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
                <Button onClick={injectHuman}>Send</Button>
              </div>
              <div className="mt-2">
                <Textarea
                  value={humanMessage}
                  onChange={(e) => setHumanMessage(e.target.value)}
                  placeholder="Type your argument..."
                  className="min-h-20"
                />
              </div>
              {socket.error ? <div className="mt-2 text-xs text-(--danger)">{socket.error}</div> : null}
            </div>
          </CardContent>
        </Card>

        {/* RIGHT: Live Analytics */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Live Analytics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="glass rounded-2xl p-3">
              <ConfidenceGauge value={confidence} />
            </div>

            <div className="glass rounded-2xl p-3">
              {socket.heatmap ? (
                <MiniHeatmap agents={socket.heatmap.agents} matrix={socket.heatmap.matrix} />
              ) : (
                <div className="text-sm text-white/55">Heatmap will appear after round end.</div>
              )}
            </div>

            <div className="glass rounded-2xl p-3">
              <StanceDistribution
                support={distribution.support}
                oppose={distribution.oppose}
                neutral={distribution.neutral}
              />
            </div>

            <div className="glass rounded-2xl p-3">
              <div className="mb-2 text-xs font-semibold tracking-wide text-white/70">Quick Stats</div>
              <div className="space-y-2 text-sm text-white/70">
                <div className="flex items-center justify-between">
                  <span className="text-white/55">Total messages</span>
                  <span className="font-semibold text-white/85">{socket.messages.length}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-white/55">Opinion shifts</span>
                  <span className="font-semibold text-white/85">{opinionShifts}</span>
                </div>
                <div className="rounded-2xl bg-black/20 p-3 ring-1 ring-white/10">
                  <div className="text-[10px] font-semibold uppercase tracking-wide text-white/45">Strongest argument</div>
                  <div className="mt-1 text-sm text-white/78">{strongestArgument}</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

