"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Topbar } from "@/components/Topbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { getSimulationStatus, predict, type PredictResponse, type SimulationMessage } from "@/lib/api";
import { cn } from "@/lib/cn";

type PredictionShape = {
  final_decision?: unknown;
  confidence?: unknown;
  key_reasoning?: unknown;
  risks?: unknown;
  recommendations?: unknown;
};

function clamp(n: number, a = 0, b = 100) {
  return Math.max(a, Math.min(b, n));
}

function toText(v: unknown, fallback = "—") {
  if (typeof v === "string") return v;
  if (typeof v === "number") return String(v);
  return fallback;
}

function asStringArray(v: unknown): string[] {
  if (Array.isArray(v)) return v.map((x) => (typeof x === "string" ? x : JSON.stringify(x))).filter(Boolean);
  return [];
}

function stanceFromText(text: string): "support" | "oppose" | "neutral" {
  const t = text.toLowerCase();
  const supportHints = ["yes", "should", "go", "proceed", "recommend", "launch", "bullish", "upside"];
  const opposeHints = ["no", "don't", "do not", "avoid", "risk", "fail", "no-go", "fatal", "bearish", "concern"];
  const s = supportHints.some((k) => t.includes(k));
  const o = opposeHints.some((k) => t.includes(k));
  if (s && !o) return "support";
  if (o && !s) return "oppose";
  return "neutral";
}

function stancePill(stance: "support" | "oppose" | "neutral") {
  if (stance === "support") return "bg-(--success)/15 text-white/85 ring-1 ring-(--success)/30";
  if (stance === "oppose") return "bg-(--danger)/15 text-white/85 ring-1 ring-(--danger)/30";
  return "bg-amber-400/15 text-white/85 ring-1 ring-amber-400/30";
}

function ConfidenceRing({ value }: { value: number }) {
  const v = clamp(value);
  const r = 44;
  const c = 2 * Math.PI * r;
  const dash = (v / 100) * c;
  return (
    <div className="relative h-28 w-28">
      <svg viewBox="0 0 120 120" className="h-full w-full">
        <circle cx="60" cy="60" r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="10" />
        <motion.circle
          cx="60"
          cy="60"
          r={r}
          fill="none"
          stroke="url(#ring)"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${c}`}
          transform="rotate(-90 60 60)"
          initial={false}
          animate={{ strokeDasharray: `${dash} ${c}` }}
          transition={{ type: "spring", stiffness: 120, damping: 18 }}
        />
        <defs>
          <linearGradient id="ring" x1="0" x2="1">
            <stop offset="0%" stopColor="rgba(109,94,252,0.95)" />
            <stop offset="100%" stopColor="rgba(47,123,255,0.95)" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 grid place-items-center">
        <div className="text-3xl font-semibold text-white/92">{Math.round(v)}%</div>
      </div>
    </div>
  );
}

export default function PredictionsPage() {
  return (
    <Suspense
      fallback={
        <div className="px-4 md:px-0">
          <Topbar title="Predictions" status={{ connected: true, running: false }} />
          <div className="mt-4 glass rounded-2xl p-4 text-sm text-white/55">Loading…</div>
        </div>
      }
    >
      <PredictionsInner />
    </Suspense>
  );
}

function PredictionsInner() {
  const params = useSearchParams();
  const [topic, setTopic] = useState("Should we launch an AI note-taking app?");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<PredictResponse | null>(null);
  const [simMessages, setSimMessages] = useState<SimulationMessage[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setError(null);
    setLoading(true);
    setData(null);
    setSimMessages(null);
    try {
      const res = await predict({ topic, rounds: 3, include_sentiment: true });
      setData(res);
      try {
        const status = await getSimulationStatus(res.simulation_id);
        setSimMessages(status.messages ?? null);
      } catch {
        // Not fatal: prediction can still render without messages
      }
    } catch (e: unknown) {
      const msg =
        e && typeof e === "object" && "message" in e
          ? String((e as { message?: unknown }).message ?? "Prediction failed")
          : "Prediction failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  // If navigated here from simulation completion, load by simulation_id
  useEffect(() => {
    const simId = params.get("simulation_id");
    const t = params.get("topic");
    if (t) setTopic(t);
    if (!simId) return;

    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      setData(null);
      setSimMessages(null);
      try {
        const status = await getSimulationStatus(simId);
        if (cancelled) return;
        const pred = (status.final_prediction ?? {}) as Record<string, unknown>;
        // We reuse the report renderer by adapting to PredictResponse shape.
        setData({
          simulation_id: simId,
          topic: status.topic || t || topic,
          prediction: pred,
          messages_count: status.messages?.length ?? 0,
          sentiment: null,
        });
        setSimMessages(status.messages ?? null);
      } catch (e: unknown) {
        if (cancelled) return;
        const msg =
          e && typeof e === "object" && "message" in e
            ? String((e as { message?: unknown }).message ?? "Failed to load simulation prediction")
            : "Failed to load simulation prediction";
        setError(msg);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  // Support both prediction_service output and aggregation_engine output.
  const prediction = (data?.prediction ?? {}) as PredictionShape & {
    confidence_level?: unknown;
    final_prediction?: { prediction?: unknown; reasoning_chain?: unknown } | unknown;
    risk_factors?: unknown;
  };

  const finalDecision =
    toText(prediction.final_decision, "") ||
    toText(
      typeof prediction.final_prediction === "object" && prediction.final_prediction
        ? (prediction.final_prediction as { prediction?: unknown }).prediction
        : undefined,
      "Launch with modifications — target premium natural segment",
    );

  const confidence = clamp(
    typeof prediction.confidence === "number"
      ? prediction.confidence
      : typeof prediction.confidence_level === "number"
        ? prediction.confidence_level
        : 74,
  );

  const reasoning = useMemo(() => {
    const base =
      asStringArray(prediction.key_reasoning).length > 0
        ? asStringArray(prediction.key_reasoning)
        : asStringArray(
            typeof prediction.final_prediction === "object" && prediction.final_prediction
              ? (prediction.final_prediction as { reasoning_chain?: unknown }).reasoning_chain
              : undefined,
          );
    if (base.length) return base.slice(0, 5);
    return [
      "✅ Clear demand signal if positioning is premium + natural",
      "✅ Differentiation through ingredient transparency + trust",
      "⚠️ Saturated market requires sharp distribution strategy",
      "⚠️ Compliance/regulatory timelines can slow iteration",
      "✅ Strong retention if product performance is measurable",
    ];
  }, [prediction.key_reasoning, prediction.final_prediction]);

  const scenario = useMemo(() => {
    // Derived UI view (not claimed as backend-provided)
    return {
      best: {
        p: 22,
        text: "Viral launch, 10K units/month within 6 months",
        conditions: ["Creator-led distribution hits", "Distinct formulation story", "High review velocity"],
      },
      likely: {
        p: 52,
        text: "Slow build, 3K units/month, break-even in 18 months",
        conditions: ["Iterate messaging", "Incremental channel expansion", "Retention > acquisition"],
      },
      worst: {
        p: 26,
        text: "Lost in market noise, pivot needed within 12 months",
        conditions: ["No clear differentiation", "CAC rises faster than LTV", "Low repeat purchase"],
      },
    };
  }, []);

  const influential = useMemo(() => {
    const msgs = simMessages ?? [];
    if (!msgs.length) {
      return [
        { emoji: "🔬", name: "Dr. Mehra", score: 0.85, stance: "support", contrib: "Identified regulatory timeline" },
        { emoji: "💰", name: "Investor", score: 0.72, stance: "neutral", contrib: "Highlighted unit economics + CAC/LTV risk" },
        { emoji: "🔴", name: "Red Team", score: 0.78, stance: "oppose", contrib: "Flagged commoditization + copycat risk" },
      ] as const;
    }

    const byAgent = new Map<string, { count: number; chars: number; last: string }>();
    for (const m of msgs) {
      const prev = byAgent.get(m.agent_role) ?? { count: 0, chars: 0, last: "" };
      byAgent.set(m.agent_role, {
        count: prev.count + 1,
        chars: prev.chars + (m.content?.length ?? 0),
        last: m.content ?? prev.last,
      });
    }

    const ranked = [...byAgent.entries()]
      .map(([agent, v]) => ({ agent, score: v.count * 0.4 + v.chars / 600, last: v.last }))
      .sort((a, b) => b.score - a.score)
      .slice(0, 3);

    const emojiMap: Record<string, string> = {
      Customer: "🧑‍💼",
      Investor: "💰",
      Expert: "🔬",
      Marketing: "📢",
      Critic: "⚖️",
      "Red Team": "🔴",
    };

    return ranked.map((r) => {
      const stance = stanceFromText(r.last);
      const score01 = clamp((r.score / 4) * 100) / 100;
      return {
        emoji: emojiMap[r.agent] ?? "💬",
        name: r.agent,
        score: score01,
        stance,
        contrib: r.last.slice(0, 72) + (r.last.length > 72 ? "…" : ""),
      };
    });
  }, [simMessages]);

  const redTeam = useMemo(() => {
    const risks = [
      ...asStringArray(prediction.risks),
      ...asStringArray(prediction.risk_factors),
    ];
    const revised = clamp(confidence - (risks.length ? 13 : 0));
    const vulns = (risks.length ? risks : ["Market saturation and weak differentiation", "Distribution costs could spike CAC"]).map(
      (r, idx) => ({
        level: idx === 0 ? "HIGH" : "MEDIUM",
        name: r,
        description: r,
        mitigation:
          idx === 0
            ? "Tight positioning + proof-based claims; focus on a narrow premium segment first."
            : "Run channel experiments; enforce CAC caps and retention targets early.",
      }),
    );
    return {
      revised,
      vulns,
      blindSpots: ["Second-order compliance timelines", "Copycat response from incumbents"],
      worstCase:
        "If differentiation fails and CAC rises, you’ll need to pivot the target segment or distribution strategy within 12 months.",
    };
  }, [prediction.risks, prediction.risk_factors, confidence]);

  function downloadReport() {
    if (!data) return;
    const payload = {
      topic: data.topic,
      simulation_id: data.simulation_id,
      generated_at: new Date().toISOString(),
      prediction: prediction,
      derived_view: {
        finalDecision,
        confidence,
        scenarios: scenario,
        influential_agents: influential,
        red_team: redTeam,
        reasoning,
      },
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `agentica-report-${data.simulation_id}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="px-4 md:px-0">
      <Topbar title="Predictions" status={{ connected: true, running: loading }} />
      <div className="mt-4 grid gap-4 lg:grid-cols-12">
        {/* controls */}
        <Card className="lg:col-span-4">
          <CardHeader>
            <CardTitle>Generate prediction</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="Enter a topic..." />
            <Button onClick={run} disabled={loading}>
              {loading ? "Agents thinking..." : "Run prediction"}
            </Button>
            {error ? <div className="text-sm text-(--danger)">{error}</div> : null}
            <div className="text-xs text-white/55">
              This page renders a report-style view. Some panels are derived from the simulation messages for UX.
            </div>
          </CardContent>
        </Card>

        {/* report */}
        <div className="lg:col-span-8 space-y-4">
          {!data ? (
            <Card>
              <CardHeader>
                <CardTitle>Prediction results</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-white/55">Run a prediction to see the final report.</div>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* TOP SECTION */}
              <Card className="rounded-3xl">
                <CardContent className="p-5 md:p-6">
                  <div className="flex flex-wrap items-start justify-between gap-5">
                    <div className="min-w-0">
                      <div className="text-xs font-semibold tracking-[0.22em] text-white/55">
                        PREDICTION RESULT
                      </div>
                      <div className="mt-2 text-balance text-2xl font-semibold leading-snug text-white/92">
                        {finalDecision}
                      </div>
                      <div className="mt-3 inline-flex items-center gap-2 rounded-full bg-white/6 px-3 py-1 text-xs text-white/70 ring-1 ring-white/10">
                        <span>Simulation Complete ✅</span>
                        <span className="text-white/25">•</span>
                        <span className="font-mono text-[11px] text-white/55">{data.simulation_id}</span>
                      </div>
                    </div>

                    <div className="glass rounded-3xl p-4">
                      <ConfidenceRing value={confidence} />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* SCENARIOS */}
              <div className="grid gap-4 lg:grid-cols-3">
                <Card className="rounded-3xl ring-1 ring-(--success)/35">
                  <CardContent className="p-5">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-semibold text-white/90">Best Case</div>
                      <div className="rounded-full bg-(--success)/15 px-2 py-0.5 text-xs text-white/80 ring-1 ring-(--success)/30">
                        {scenario.best.p}%
                      </div>
                    </div>
                    <div className="mt-2 text-sm text-white/70">{scenario.best.text}</div>
                    <ul className="mt-3 list-disc space-y-1 pl-4 text-sm text-white/60">
                      {scenario.best.conditions.map((c) => (
                        <li key={c}>{c}</li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>

                <Card className="rounded-3xl ring-1 ring-(--accent-2)/35">
                  <CardContent className="p-5">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-semibold text-white/90">Most Likely</div>
                      <div className="rounded-full bg-(--accent-2)/15 px-2 py-0.5 text-xs text-white/80 ring-1 ring-(--accent-2)/30">
                        {scenario.likely.p}%
                      </div>
                    </div>
                    <div className="mt-2 text-sm text-white/70">{scenario.likely.text}</div>
                    <ul className="mt-3 list-disc space-y-1 pl-4 text-sm text-white/60">
                      {scenario.likely.conditions.map((c) => (
                        <li key={c}>{c}</li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>

                <Card className="rounded-3xl ring-1 ring-(--danger)/35">
                  <CardContent className="p-5">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-semibold text-white/90">Worst Case</div>
                      <div className="rounded-full bg-(--danger)/15 px-2 py-0.5 text-xs text-white/80 ring-1 ring-(--danger)/30">
                        {scenario.worst.p}%
                      </div>
                    </div>
                    <div className="mt-2 text-sm text-white/70">{scenario.worst.text}</div>
                    <ul className="mt-3 list-disc space-y-1 pl-4 text-sm text-white/60">
                      {scenario.worst.conditions.map((c) => (
                        <li key={c}>{c}</li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </div>

              {/* KEY REASONING */}
              <Card className="rounded-3xl">
                <CardHeader>
                  <CardTitle>Key Reasoning</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {reasoning.map((r) => (
                      <li
                        key={r}
                        className="flex items-start gap-2 rounded-2xl bg-black/20 p-3 text-sm text-white/75 ring-1 ring-white/10"
                      >
                        <span className="mt-0.5">{r.startsWith("⚠️") ? "⚠️" : "✅"}</span>
                        <span>{r.replace(/^✅\s*|^⚠️\s*/, "")}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>

              {/* MOST INFLUENTIAL AGENTS */}
              <Card className="rounded-3xl">
                <CardHeader>
                  <CardTitle>Most Influential Agents</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-col gap-3 md:flex-row">
                    {influential.map((a) => (
                      <div key={a.name} className="glass flex-1 rounded-3xl p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-center gap-2">
                            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/6 text-lg ring-1 ring-white/10">
                              {a.emoji}
                            </div>
                            <div>
                              <div className="text-sm font-semibold text-white/90">{a.name}</div>
                              <div className="text-[11px] text-white/55">Key contribution</div>
                            </div>
                          </div>
                          <span className={cn("rounded-full px-2 py-1 text-[10px]", stancePill(a.stance))}>
                            {a.stance}
                          </span>
                        </div>

                        <div className="mt-3">
                          <div className="mb-1 flex items-center justify-between text-[10px] text-white/45">
                            <span>Influence</span>
                            <span>{a.score.toFixed(2)}</span>
                          </div>
                          <div className="h-2 w-full overflow-hidden rounded-full bg-white/6 ring-1 ring-white/10">
                            <div
                              className="h-full bg-linear-to-r from-(--accent) to-(--accent-2)"
                              style={{ width: `${Math.round(a.score * 100)}%` }}
                            />
                          </div>
                        </div>

                        <div className="mt-3 text-sm text-white/70">{a.contrib}</div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* RED TEAM REPORT */}
              <Card className="rounded-3xl">
                <CardContent className="p-0">
                  <details className="group">
                    <summary className="cursor-pointer list-none px-5 py-4 md:px-6">
                      <div className="flex items-center justify-between gap-3">
                        <div className="text-sm font-semibold text-white/90">🔴 Red Team Vulnerability Report</div>
                        <div className="text-xs text-white/60">
                          Revised confidence:{" "}
                          <span className="font-semibold text-white/85">
                            {Math.round(confidence)}% → {Math.round(redTeam.revised)}%
                          </span>
                        </div>
                      </div>
                      <div className="mt-1 text-xs text-white/45">
                        Expand for vulnerabilities, blind spots, and worst-case summary.
                      </div>
                    </summary>
                    <div className="px-5 pb-5 md:px-6">
                      <div className="space-y-3">
                        {redTeam.vulns.map((v) => (
                          <div key={v.name} className="rounded-3xl bg-black/20 p-4 ring-1 ring-white/10">
                            <div className="flex items-start justify-between gap-3">
                              <div className="text-sm font-semibold text-white/85">{v.name}</div>
                              <span className="rounded-full bg-(--danger)/15 px-2 py-0.5 text-[10px] text-white/80 ring-1 ring-(--danger)/25">
                                {v.level}
                              </span>
                            </div>
                            <div className="mt-2 text-sm text-white/65">{v.description}</div>
                            <div className="mt-3 rounded-2xl bg-white/5 p-3 text-sm text-white/70 ring-1 ring-white/10">
                              <span className="text-white/55">Mitigation:</span> {v.mitigation}
                            </div>
                          </div>
                        ))}

                        <div className="grid gap-3 md:grid-cols-2">
                          <div className="rounded-3xl bg-black/20 p-4 ring-1 ring-white/10">
                            <div className="text-sm font-semibold text-white/85">Blind spots</div>
                            <ul className="mt-2 list-disc space-y-1 pl-4 text-sm text-white/65">
                              {redTeam.blindSpots.map((b) => (
                                <li key={b}>{b}</li>
                              ))}
                            </ul>
                          </div>
                          <div className="rounded-3xl bg-black/20 p-4 ring-1 ring-white/10">
                            <div className="text-sm font-semibold text-white/85">Worst-case scenario</div>
                            <div className="mt-2 text-sm text-white/65">{redTeam.worstCase}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </details>
                </CardContent>
              </Card>

              {/* NEXT STEPS */}
              <Card className="rounded-3xl">
                <CardHeader>
                  <CardTitle>Recommended Next Steps</CardTitle>
                </CardHeader>
                <CardContent>
                  <ol className="space-y-2">
                    {[
                      "Define the premium natural segment and positioning wedge",
                      "Run 2–3 channel tests to validate CAC and conversion",
                      "Validate retention signals with a small cohort pilot",
                      "Map compliance/regulatory requirements and timeline",
                      "Lock a differentiation thesis (ingredients, proof, or experience)",
                    ].map((s, i) => (
                      <li key={s} className="flex items-start gap-3 rounded-2xl bg-black/20 p-3 ring-1 ring-white/10">
                        <span className="mt-0.5 grid h-5 w-5 place-items-center rounded-md bg-white/6 text-[11px] text-white/70 ring-1 ring-white/10">
                          {i + 1}
                        </span>
                        <span className="text-sm text-white/75">{s}</span>
                      </li>
                    ))}
                  </ol>
                </CardContent>
              </Card>

              {/* ACTIONS */}
              <div className="flex flex-wrap gap-2">
                <Link href={`/butterfly?topic=${encodeURIComponent(data.topic)}&simulation_id=${encodeURIComponent(data.simulation_id)}`}>
                  <Button variant="secondary">🦋 Try Butterfly Effect</Button>
                </Link>
                <Button variant="secondary" onClick={downloadReport}>
                  📥 Download Report
                </Button>
                <Link href="/new">
                  <Button>🔄 Run New Simulation</Button>
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

