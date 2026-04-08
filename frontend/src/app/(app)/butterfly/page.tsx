"use client";

import { useState } from "react";
import { Topbar } from "@/components/Topbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { butterflyEffect, type ButterflyResponse } from "@/lib/api";

export default function ButterflyPage() {
  const [topic, setTopic] = useState("Should we launch an AI note-taking app?");
  const [simulationId, setSimulationId] = useState("");
  const [alternative, setAlternative] = useState(
    "Change pricing to $4.99/month and launch to students first; how does that impact adoption and revenue?",
  );
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ButterflyResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setError(null);
    setLoading(true);
    setData(null);
    try {
      const res = await butterflyEffect({
        topic,
        simulation_id: simulationId.trim(),
        alternative_scenario: alternative.trim(),
      });
      setData(res);
    } catch (e: unknown) {
      const msg =
        e && typeof e === "object" && "message" in e
          ? String((e as { message?: unknown }).message ?? "Butterfly analysis failed")
          : "Butterfly analysis failed";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="px-4 md:px-0">
      <Topbar title="Butterfly Effect" status={{ connected: true, running: loading }} />
      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Compare scenarios</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <Input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="Base topic..." />
            <Input
              value={simulationId}
              onChange={(e) => setSimulationId(e.target.value)}
              placeholder="Existing simulation_id (required)"
            />
            <Textarea value={alternative} onChange={(e) => setAlternative(e.target.value)} />
            <Button onClick={run} disabled={loading || !simulationId.trim()}>
              {loading ? "Analyzing..." : "Run butterfly analysis"}
            </Button>
            {error ? <div className="text-sm text-(--danger)">{error}</div> : null}
            <div className="text-xs text-white/55">
              Backend route is <code>/api/predict/butterfly-effect</code> and requires an existing in-memory simulation.
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            {data ? (
              <pre className="max-h-[640px] overflow-auto rounded-2xl bg-black/30 p-3 text-xs text-white/75 ring-1 ring-white/10">
                {JSON.stringify(data.analysis, null, 2)}
              </pre>
            ) : (
              <div className="text-sm text-white/55">
                Paste a <code>simulation_id</code> from a previous run, then submit an alternative scenario.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

