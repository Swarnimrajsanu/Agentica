"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/cn";

const features = [
  {
    title: "🔴 Red Team Agent",
    desc: "Adversarial stress testing of your decisions",
  },
  {
    title: "🗺️ Decision Tree",
    desc: "Visual reasoning trace of every argument",
  },
  {
    title: "📊 Consensus Heatmap",
    desc: "See who agrees and disagrees in real-time",
  },
  {
    title: "🧑‍💻 Human-as-an-Agent",
    desc: "Join the simulation and argue with AI",
  },
  {
    title: "🦋 Butterfly Effect",
    desc: "Change one variable, see everything shift",
  },
];

const steps = [
  "Seed Input",
  "GraphRAG",
  "Agent Spawn",
  "Simulation",
  "Memory",
  "LLM Reasoning",
  "Prediction",
];

const agents = [
  {
    emoji: "🧑‍💼",
    name: "Customer Agent",
    role: "Market-fit lens",
    personality: "cautious",
    bias: "prefers simple, valuable outcomes",
  },
  {
    emoji: "💰",
    name: "Investor Agent",
    role: "ROI + moat lens",
    personality: "analytical",
    bias: "optimizes for scalable upside",
  },
  {
    emoji: "🔬",
    name: "Expert Agent",
    role: "Technical validity",
    personality: "data-driven",
    bias: "demands evidence and feasibility",
  },
  {
    emoji: "📢",
    name: "Marketing Agent",
    role: "Positioning + growth",
    personality: "creative",
    bias: "seeks narrative and distribution edge",
  },
  {
    emoji: "⚖️",
    name: "Critic Agent",
    role: "Assumption checking",
    personality: "contrarian",
    bias: "targets weak links and blind spots",
  },
  {
    emoji: "🔴",
    name: "Red Team Agent",
    role: "Adversarial pressure",
    personality: "adversarial",
    bias: "prefers worst-case scrutiny",
  },
];

const useCases = [
  { title: "Business Strategy", desc: "Simulate stakeholder dynamics before committing resources." },
  { title: "Product Launch", desc: "Test pricing, positioning, and rollout scenarios." },
  { title: "Investment Decision", desc: "Stress-test thesis, risks, and alternative outcomes." },
  { title: "Policy Analysis", desc: "Explore second-order effects across groups and constraints." },
];

function Glow({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "pointer-events-none absolute inset-0 opacity-70",
        className,
      )}
    >
      <div className="absolute -top-20 left-[10%] h-72 w-72 rounded-full bg-(--accent)/25 blur-3xl" />
      <div className="absolute -top-24 right-[8%] h-80 w-80 rounded-full bg-(--accent-2)/20 blur-3xl" />
      <div className="absolute bottom-[-120px] left-[35%] h-96 w-96 rounded-full bg-(--accent)/15 blur-3xl" />
    </div>
  );
}

function AnimatedGrid() {
  return (
    <div className="pointer-events-none absolute inset-0">
      <div
        className="absolute inset-0 opacity-[0.22]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.06) 1px, transparent 1px)",
          backgroundSize: "46px 46px",
          maskImage:
            "radial-gradient(circle at 50% 10%, black 0%, black 35%, transparent 72%)",
          WebkitMaskImage:
            "radial-gradient(circle at 50% 10%, black 0%, black 35%, transparent 72%)",
        }}
      />
      <motion.div
        aria-hidden
        className="absolute inset-0 opacity-[0.08]"
        animate={{ backgroundPositionX: ["0px", "180px"] }}
        transition={{ duration: 14, repeat: Infinity, ease: "linear" }}
        style={{
          backgroundImage:
            "linear-gradient(90deg, rgba(109,94,252,0.35) 0%, rgba(47,123,255,0.0) 55%)",
          backgroundSize: "220px 220px",
        }}
      />
    </div>
  );
}

function ParticleField() {
  const dots = Array.from({ length: 18 }).map((_, i) => {
    const left = (i * 57) % 100;
    const top = (i * 37) % 70;
    const size = 2 + (i % 3);
    const delay = (i % 7) * 0.4;
    const dur = 4 + (i % 5);
    return { left, top, size, delay, dur, key: i };
  });

  return (
    <div className="pointer-events-none absolute inset-0">
      {dots.map((d) => (
        <motion.div
          key={d.key}
          className="absolute rounded-full bg-white/60"
          style={{
            left: `${d.left}%`,
            top: `${d.top}%`,
            width: d.size,
            height: d.size,
            filter: "drop-shadow(0 0 10px rgba(47,123,255,0.35))",
          }}
          animate={{ y: [0, -10, 0], opacity: [0.25, 0.8, 0.25] }}
          transition={{ duration: d.dur, delay: d.delay, repeat: Infinity, ease: "easeInOut" }}
        />
      ))}
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="relative overflow-hidden">
        <Glow />
        <AnimatedGrid />
        <ParticleField />

        <div className="mx-auto max-w-[1200px] px-5 pb-16 pt-10 md:pb-24 md:pt-14">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-2xl bg-linear-to-br from-(--accent) to-(--accent-2) shadow-[0_18px_70px_rgba(47,123,255,0.18)]" />
              <div className="text-lg font-semibold tracking-wide text-white/90">
                <span className="font-bold">Agentica</span>
              </div>
            </div>
            <div className="hidden md:flex items-center gap-2">
              <Link href="/dashboard">
                <Button variant="ghost">Dashboard</Button>
              </Link>
              <Link href="/new">
                <Button variant="secondary">Start Simulation</Button>
              </Link>
            </div>
          </div>

          <div className="mt-12 grid gap-10 md:mt-16 md:grid-cols-2 md:gap-12">
            <div>
              <motion.h1
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35 }}
                className="text-balance text-4xl font-semibold leading-tight text-white/95 md:text-5xl"
              >
                Don&apos;t just ask AI.
                <span className="block bg-gradient-to-r from-(--accent) to-(--accent-2) bg-clip-text text-transparent">
                  Simulate intelligence.
                </span>
              </motion.h1>

              <motion.p
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: 0.06 }}
                className="mt-5 max-w-xl text-base leading-relaxed text-white/65"
              >
                Multiple AI agents debate your decision. Get structured predictions with confidence scores,
                scenarios, and reasoning traces.
              </motion.p>

              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: 0.12 }}
                className="mt-8 flex flex-wrap items-center gap-3"
              >
                <Link href="/new">
                  <Button size="lg" className="shadow-[0_18px_70px_rgba(109,94,252,0.22)]">
                    Start Simulation
                  </Button>
                </Link>
                <Link href="/simulation?topic=Should%20we%20launch%20an%20AI%20note-taking%20app%3F">
                  <Button size="lg" variant="secondary">
                    Watch Demo
                  </Button>
                </Link>
                <div className="text-xs text-white/45">
                  Real-time simulation • Human-in-the-loop • Predictions
                </div>
              </motion.div>
            </div>

            <motion.div
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.35, delay: 0.12 }}
              className="relative"
            >
              <div className="glass rounded-3xl p-4 shadow-[0_30px_120px_rgba(0,0,0,0.45)]">
                <div className="flex items-center justify-between">
                  <div className="text-xs font-semibold tracking-wide text-white/75">Live simulation preview</div>
                  <div className="rounded-full bg-white/6 px-2 py-1 text-[10px] text-white/55 ring-1 ring-white/10">
                    streaming
                  </div>
                </div>

                <div className="mt-3 space-y-2">
                  {[
                    { who: "Customer", txt: "I’d use it if it saves time and feels effortless." },
                    { who: "Investor", txt: "Differentiation + retention will decide ROI." },
                    { who: "Critic", txt: "What’s the moat? Many apps will copy features." },
                    { who: "Human", txt: "Ship to students first, optimize habit loops, then expand." },
                  ].map((m, i) => (
                    <div key={i} className="rounded-2xl bg-black/20 p-3 ring-1 ring-white/10">
                      <div className="text-[10px] font-semibold uppercase tracking-wide text-white/45">
                        {m.who}
                      </div>
                      <div className="mt-1 text-sm text-white/78">{m.txt}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pointer-events-none absolute -inset-6 -z-10 rounded-[32px] bg-gradient-to-r from-(--accent)/25 to-(--accent-2)/15 blur-3xl" />
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-[1200px] px-5 py-14 md:py-20">
        <div className="flex items-end justify-between gap-6">
          <div>
            <div className="text-sm font-semibold tracking-wide text-white/80">Features</div>
            <div className="mt-2 text-2xl font-semibold text-white/92">Everything you need to simulate outcomes</div>
            <div className="mt-2 max-w-2xl text-sm text-white/55">
              Agentica doesn’t output a single answer — it runs a debate, measures agreement, and produces a structured
              prediction you can act on.
            </div>
          </div>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {features.map((f) => (
            <Card key={f.title} className="rounded-3xl p-4">
              <div className="text-sm font-semibold text-white/90">{f.title}</div>
              <div className="mt-2 text-sm text-white/60">{f.desc}</div>
              <div className="mt-4 h-px w-full bg-gradient-to-r from-white/0 via-white/10 to-white/0" />
              <div className="mt-3 text-xs text-white/45">
                Real-time • composable • designed for decision makers
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="mx-auto max-w-[1200px] px-5 pb-14 md:pb-20">
        <div className="glass rounded-3xl p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold tracking-wide text-white/80">How it works</div>
              <div className="mt-2 text-xl font-semibold text-white/92">A 7-step pipeline from idea to prediction</div>
            </div>
            <Link href="/new">
              <Button variant="secondary">Try it now</Button>
            </Link>
          </div>

          <div className="mt-6 overflow-x-auto">
            <div className="flex min-w-[920px] items-center gap-3">
              {steps.map((s, idx) => (
                <div key={s} className="flex items-center gap-3">
                  <div className="rounded-2xl bg-white/6 px-4 py-3 ring-1 ring-white/10">
                    <div className="text-[10px] font-semibold uppercase tracking-wide text-white/45">
                      Step {idx + 1}
                    </div>
                    <div className="mt-1 text-sm font-semibold text-white/85">{s}</div>
                  </div>
                  {idx < steps.length - 1 ? (
                    <div className="h-[2px] w-10 bg-gradient-to-r from-(--accent)/50 to-(--accent-2)/40 opacity-70" />
                  ) : null}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Agent showcase */}
      <section className="mx-auto max-w-[1200px] px-5 pb-14 md:pb-20">
        <div className="flex items-end justify-between gap-6">
          <div>
            <div className="text-sm font-semibold tracking-wide text-white/80">Agents</div>
            <div className="mt-2 text-2xl font-semibold text-white/92">A panel of perspectives, not one voice</div>
            <div className="mt-2 max-w-2xl text-sm text-white/55">
              Each agent has a role, personality, and bias — so you can see how different stakeholders would react.
            </div>
          </div>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {agents.map((a) => (
            <Card key={a.name} className="rounded-3xl p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/6 text-xl ring-1 ring-white/10">
                    {a.emoji}
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-white/90">{a.name}</div>
                    <div className="text-xs text-white/55">{a.role}</div>
                  </div>
                </div>
                <div className="rounded-full bg-white/6 px-2 py-1 text-[10px] text-white/55 ring-1 ring-white/10">
                  {a.personality}
                </div>
              </div>

              <div className="mt-4 grid gap-2 text-xs">
                <div className="flex items-center justify-between rounded-2xl bg-black/20 px-3 py-2 ring-1 ring-white/10">
                  <span className="text-white/50">Personality</span>
                  <span className="text-white/80">{a.personality}</span>
                </div>
                <div className="rounded-2xl bg-black/20 px-3 py-2 text-white/70 ring-1 ring-white/10">
                  <span className="text-white/50">Bias</span>
                  <div className="mt-1 text-white/78">{a.bias}</div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* Use cases */}
      <section className="mx-auto max-w-[1200px] px-5 pb-14 md:pb-20">
        <div className="glass rounded-3xl p-6">
          <div className="text-sm font-semibold tracking-wide text-white/80">Use Cases</div>
          <div className="mt-2 text-xl font-semibold text-white/92">Built for real decisions</div>
          <div className="mt-5 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {useCases.map((u) => (
              <div key={u.title} className="rounded-3xl bg-black/20 p-4 ring-1 ring-white/10">
                <div className="text-sm font-semibold text-white/88">{u.title}</div>
                <div className="mt-2 text-sm text-white/60">{u.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10">
        <div className="mx-auto flex max-w-[1200px] flex-col gap-4 px-5 py-10 md:flex-row md:items-center md:justify-between">
          <div className="text-sm text-white/60">
            <span className="font-semibold text-white/80">Agentica</span> — Don&apos;t just ask AI. Simulate
            intelligence.
          </div>
          <div className="flex flex-wrap items-center gap-3 text-sm text-white/55">
            <Link className="hover:text-white/80" href="/dashboard">
              App
            </Link>
            <Link className="hover:text-white/80" href="/new">
              Start
            </Link>
            <a className="hover:text-white/80" href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
              API Docs
            </a>
            <span className="text-white/25">•</span>
            <span className="text-white/45">© {new Date().getFullYear()} Agentica</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

