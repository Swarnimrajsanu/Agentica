"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Topbar } from "@/components/Topbar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";

export default function NewSimulationPage() {
  const router = useRouter();
  const [topic, setTopic] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function start() {
    setError(null);
    const t = topic.trim();
    if (!t) return setError("Please enter an idea/topic.");
    setLoading(true);
    try {
      // For the real-time page we use the websocket simulate endpoint,
      // so we just navigate and let the stream run.
      router.push(`/simulation?topic=${encodeURIComponent(t)}`);
    } catch {
      setError("Failed to start simulation.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="px-4 md:px-0">
      <Topbar title="New Simulation" status={{ connected: true, running: false }} />
      <div className="mt-4">
        <Card>
          <CardHeader>
            <CardTitle>Enter your idea</CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Enter your idea..."
            />
            {error ? <div className="mt-2 text-sm text-(--danger)">{error}</div> : null}
            <div className="mt-3 flex items-center gap-3">
              <Button onClick={start} disabled={loading}>
                {loading ? "Agents thinking..." : "Start Simulation"}
              </Button>
              <div className="text-xs text-white/50">
                Tip: you can inject a human argument live from the Simulation page.
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

