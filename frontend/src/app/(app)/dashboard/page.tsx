"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function DashboardPage() {
  // Production note: these should come from backend analytics.
  const kpis = [
    { label: "Active Agents", value: "5" },
    { label: "Simulations Run", value: "—" },
    { label: "Predictions Generated", value: "—" },
  ];

  return (
    <div className="px-4 md:px-0">
      <div className="pt-4 md:pt-6">
        <div className="glass rounded-2xl px-4 py-4 md:px-6 md:py-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-lg font-semibold text-white/90">Dashboard</div>
              <div className="text-sm text-white/55">Your command center for multi-agent simulations.</div>
            </div>
            <Link href="/new">
              <Button size="lg">Start New Simulation</Button>
            </Link>
          </div>
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {kpis.map((k) => (
            <Card key={k.label}>
              <CardHeader>
                <CardTitle>{k.label}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-semibold text-white/90">{k.value}</div>
                <div className="mt-1 text-xs text-white/45">Live metrics (hook up analytics later)</div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Simulations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-white/60">
                Run a simulation to see it appear here. (This backend currently stores simulations in-memory per server
                session.)
              </div>
              <div className="mt-3">
                <Link href="/new">
                  <Button variant="secondary">Start New Simulation</Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

