"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { SimulationMessage } from "@/lib/api";

type SocketEvent =
  | { type: "connected"; client_id?: string; message?: string }
  | { type: "simulation_starting"; topic: string; message?: string }
  | { type: "agents_spawned"; agents?: Array<{ role: string; personality?: string }>; agents_count?: number }
  | { type: "round_start"; round: number; total_rounds?: number }
  | { type: "agent_response"; message: SimulationMessage }
  | { type: "human_injected"; message: SimulationMessage }
  | { type: "consensus_heatmap"; round: number; agents: string[]; matrix: number[][] }
  | { type: "prediction_update"; round: number; consensus: unknown; prediction: unknown }
  | { type: "round_end"; round: number }
  | {
      type: "simulation_complete";
      message?: string;
      result?: {
        simulation_id?: string;
        status?: string;
        messages_count?: number;
        consensus?: unknown;
        final_prediction?: unknown;
      };
    }
  | { type: "graph_update"; nodes: any[]; links: any[]; agent?: string }
  | { type: "error"; message?: string };

export type UseSimulationSocketState = {
  connected: boolean;
  running: boolean;
  round: number | null;
  messages: SimulationMessage[];
  graphData: { nodes: any[]; links: any[] };
  heatmap?: { round: number; agents: string[]; matrix: number[][] };
  predictionUpdate?: { round: number; consensus: unknown; prediction: unknown };
  completed?: { simulation_id?: string; final_prediction?: unknown };
  error?: string;
  sendHumanMessage: (args: { message: string; influence_level?: number; display_name?: string }) => void;
  close: () => void;
};

const WS_BASE =
  process.env.NEXT_PUBLIC_WS_BASE?.replace(/\/+$/, "") || "ws://localhost:8000/api";

export function useSimulationSocket(topic: string): UseSimulationSocketState {
  const [connected, setConnected] = useState(false);
  const [running, setRunning] = useState(false);
  const [round, setRound] = useState<number | null>(null);
  const [messages, setMessages] = useState<SimulationMessage[]>([]);
  const [graphData, setGraphData] = useState<{ nodes: any[]; links: any[] }>({ nodes: [], links: [] });
  const [heatmap, setHeatmap] = useState<UseSimulationSocketState["heatmap"]>();
  const [predictionUpdate, setPredictionUpdate] =
    useState<UseSimulationSocketState["predictionUpdate"]>();
  const [completed, setCompleted] = useState<UseSimulationSocketState["completed"]>();
  const [error, setError] = useState<string | undefined>();

  const wsRef = useRef<WebSocket | null>(null);
  const topicForWs = useMemo(() => topic.trim().replace(/\s+/g, "_"), [topic]);

  useEffect(() => {
    if (!topicForWs) return;

    const url = `${WS_BASE}/ws/simulate/${encodeURIComponent(topicForWs)}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      setError(undefined);
    };

    ws.onclose = () => {
      setConnected(false);
      setRunning(false);
    };

    ws.onerror = () => {
      setError("WebSocket error");
      setConnected(false);
    };

    ws.onmessage = (evt) => {
      let data: SocketEvent | null = null;
      try {
        data = JSON.parse(evt.data) as SocketEvent;
      } catch {
        return;
      }

      if (!data) return;

      if (data.type === "simulation_starting") {
        setRunning(true);
        setMessages([]);
        setGraphData({ nodes: [], links: [] });
        setRound(null);
        setCompleted(undefined);
      }

      if (data.type === "round_start") setRound(data.round);
      if (data.type === "round_end") setRound(data.round);

      if (data.type === "agent_response" || data.type === "human_injected") {
        setMessages((prev) => [...prev, data.message]);
      }

      if (data.type === "graph_update") {
        setGraphData((prev) => {
          const nodeMap = new Map(prev.nodes.map((n: any) => [n.id, n]));
          data.nodes.forEach((n: any) => nodeMap.set(n.id, n));
          return {
            nodes: Array.from(nodeMap.values()),
            links: [...prev.links, ...(data.links || [])],
          };
        });
      }

      if (data.type === "consensus_heatmap") {
        setHeatmap({ round: data.round, agents: data.agents, matrix: data.matrix });
      }

      if (data.type === "prediction_update") {
        setPredictionUpdate({ round: data.round, consensus: data.consensus, prediction: data.prediction });
      }

      if (data.type === "simulation_complete") {
        setRunning(false);
        setCompleted({
          simulation_id: data.result?.simulation_id,
          final_prediction: data.result?.final_prediction,
        });
      }

      if (data.type === "error") {
        setError(data.message || "Unknown error");
      }
    };

    return () => {
      try {
        ws.close();
      } catch {}
      wsRef.current = null;
    };
  }, [topicForWs]);

  const sendHumanMessage = useCallback(
    (args: { message: string; influence_level?: number; display_name?: string }) => {
      const ws = wsRef.current;
      if (!ws || ws.readyState !== WebSocket.OPEN) return;
      ws.send(
        JSON.stringify({
          type: "human_message",
          message: args.message,
          influence_level: args.influence_level ?? 0.6,
          display_name: args.display_name ?? "Human",
        }),
      );
    },
    [],
  );

  const close = useCallback(() => {
    try {
      wsRef.current?.send(JSON.stringify({ type: "close" }));
      wsRef.current?.close();
    } catch {}
  }, []);

  return {
    connected,
    running,
    round,
    messages,
    graphData,
    heatmap,
    predictionUpdate,
    completed,
    error,
    sendHumanMessage,
    close,
  };
}

