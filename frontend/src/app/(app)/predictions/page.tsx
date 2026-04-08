"use client";

import { useState } from "react";
import { Topbar } from "@/components/Topbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { predict, type PredictResponse } from "@/lib/api";
import { PredictionCard } from "@/components/PredictionCard";

export default function PredictionsPage() {
  const [topic, setTopic] = useState("Should we launch an AI note-taking app?");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<PredictResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setError(null);
    setLoading(true);
    setData(null);
    try {
      const res = await predict({ topic, rounds: 3, include_sentiment: true });
      setData(res);
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

  return (
    <div className="px-4 md:px-0">
      <Topbar title="Predictions" status={{ connected: true, running: loading }} />
      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Generate prediction</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="Enter a topic..." />
              <Button onClick={run} disabled={loading}>
                {loading ? "Agents thinking..." : "Run /predict"}
              </Button>
              {error ? <div className="text-sm text-(--danger)">{error}</div> : null}
              <div className="text-xs text-white/55">
                This endpoint runs a simulation + returns prediction, confidence, and reasoning.
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="lg:col-span-2 space-y-4">
          {data ? (
            <>
              <PredictionCard title="Prediction" subtitle={`simulation_id: ${data.simulation_id}`} data={data.prediction} />
              {data.sentiment ? <PredictionCard title="Sentiment" data={data.sentiment} /> : null}
            </>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Result</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-white/55">Run a prediction to see results here.</div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

