"use client";

import { useEffect, useState } from "react";
import { Topbar } from "@/components/Topbar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RedTeamReport } from "@/components/RedTeamReport";
import { useSimulationSocket } from "@/hooks/useSimulationSocket";
import { ShieldAlert, Terminal, Activity } from "lucide-react";

export default function RedTeamPage() {
  const [activeTopic, setActiveTopic] = useState<string | null>(null);
  
  // Fetch currently active simulation to follow
  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api"}/simulate/active`)
      .then(res => res.json())
      .then(data => {
        if (data.active_simulations && data.active_simulations.length > 0) {
          setActiveTopic(data.active_simulations[0].topic);
        }
      });
  }, []);

  const socket = useSimulationSocket(activeTopic || "");

  return (
    <div className="flex flex-col gap-6 p-6">
      <Topbar 
        title="Red Team: Adversarial Analysis" 
        status={{ connected: socket.connected, running: socket.running }} 
      />

      <div className="grid gap-6 lg:grid-cols-12">
        {/* LEFT: Live Log */}
        <div className="lg:col-span-4 space-y-6">
          <Card className="h-full">
            <CardHeader className="border-b border-white/5">
              <CardTitle className="flex items-center gap-2 text-red-500">
                <Terminal size={18} /> Adversarial Stream
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 overflow-auto max-h-[600px] font-mono text-[10px] space-y-2">
              {!activeTopic ? (
                  <div className="text-white/20 italic">No active simulation detected to monitor...</div>
              ) : (
                  <>
                    <div className="text-green-500">[SYSTEM] Monitoring active topic: {activeTopic}</div>
                    <div className="text-blue-500">[SCAN] Injection vectors initialized.</div>
                    {socket.messages.slice(-5).map((m, i) => (
                        <div key={i} className="text-white/40">
                            [AGENT_MSG] {m.agent_role}: {m.content.slice(0, 50)}...
                        </div>
                    ))}
                    {socket.redTeamData && (
                        <div className="text-red-500 animate-pulse">
                            [RED_TEAM] Vulnerabilities detected in Round {socket.round || "?"}
                        </div>
                    )}
                  </>
              )}
            </CardContent>
          </Card>
        </div>

        {/* RIGHT: Main Report */}
        <div className="lg:col-span-8 space-y-6">
          <Card className="bg-red-500/5 border-red-500/20">
            <CardContent className="p-6">
              {!activeTopic ? (
                <div className="flex flex-col items-center justify-center h-[400px] text-center space-y-4">
                  <ShieldAlert size={48} className="text-white/10" />
                  <div>
                    <h3 className="text-lg font-bold text-white/50">System Idle</h3>
                    <p className="text-sm text-white/30">Start or join a simulation to begin live adversarial analysis.</p>
                  </div>
                </div>
              ) : (
                <RedTeamReport data={socket.redTeamData} />
              )}
            </CardContent>
          </Card>

          {activeTopic && (
              <div className="flex items-center gap-2 text-[10px] text-white/20 uppercase tracking-[0.2em] justify-center">
                  <Activity size={12} className="text-red-500 animate-pulse" /> Live Analysis Active
              </div>
          )}
        </div>
      </div>
    </div>
  );
}
