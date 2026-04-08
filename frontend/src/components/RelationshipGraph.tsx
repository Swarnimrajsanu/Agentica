"use client";

import React, { useEffect, useRef, useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface Node {
  id: string;
  label: string;
  type: "agent" | "concept" | "risk" | "opportunity";
  x: number;
  y: number;
  vx: number;
  vy: number;
  color?: string;
  size: number;
}

interface Link {
  source: string;
  target: string;
  label?: string;
}

interface RelationshipGraphProps {
  messages: any[];
  graphData: { nodes: any[]; links: any[] };
}

export function RelationshipGraph({ messages, graphData }: RelationshipGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [links, setLinks] = useState<Link[]>([]);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  // Update dimensions
  useEffect(() => {
    if (!containerRef.current) return;
    const resizeObserver = new ResizeObserver((entries) => {
      for (let entry of entries) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });
    resizeObserver.observe(containerRef.current);
    return () => resizeObserver.disconnect();
  }, []);

  // Sync nodes and links from graphData and messages
  useEffect(() => {
    setNodes((prev) => {
      const nodeMap = new Map(prev.map((n) => [n.id, n]));
      
      // 1. Add agent nodes from messages if they don't exist
      const agents = Array.from(new Set(messages.map((m) => m.agent_role)));
      agents.forEach((agentId: any) => {
        if (!nodeMap.has(agentId)) {
          nodeMap.set(agentId, {
            id: agentId,
            label: agentId,
            type: "agent",
            x: Math.random() * (dimensions.width || 400),
            y: Math.random() * (dimensions.height || 400),
            vx: 0,
            vy: 0,
            size: 44,
          });
        }
      });

      // 2. Add nodes from graphData
      (graphData.nodes || []).forEach((n: any) => {
        if (!nodeMap.has(n.id)) {
          nodeMap.set(n.id, {
            ...n,
            label: n.label || n.id,
            type: n.type || "concept",
            x: Math.random() * (dimensions.width || 400),
            y: Math.random() * (dimensions.height || 400),
            vx: 0,
            vy: 0,
            size: 32,
          });
        }
      });

      return Array.from(nodeMap.values());
    });

    setLinks((prev) => {
        const linkKeys = new Set(prev.map(l => `${l.source}-${l.target}`));
        const newLinks = [...prev];
        
        (graphData.links || []).forEach((l: any) => {
            const key = `${l.source}-${l.target}`;
            if (!linkKeys.has(key)) {
                linkKeys.add(key);
                newLinks.push(l);
            }
        });
        
        return newLinks;
    });
  }, [messages, graphData, dimensions.width, dimensions.height]);

  // Simulation Loop (Simple Spring Force)
  useEffect(() => {
    let animationFrameId: number;
    const strength = 0.05;
    const distance = 100;

    const tick = () => {
      setNodes((prevNodes) => {
        if (!prevNodes.length) return prevNodes;

        const nextNodes = prevNodes.map((n) => ({ ...n }));

        // Center force
        const centerX = dimensions.width / 2;
        const centerY = dimensions.height / 2;

        for (let n of nextNodes) {
          n.vx += (centerX - n.x) * 0.001;
          n.vy += (centerY - n.y) * 0.001;
        }

        // Link forces
        links.forEach((link) => {
          const source = nextNodes.find((n) => n.id === link.source);
          const target = nextNodes.find((n) => n.id === link.target);
          if (!source || !target) return;

          const dx = target.x - source.x;
          const dy = target.y - source.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const diff = (dist - distance) / dist;
          const fx = dx * diff * strength;
          const fy = dy * diff * strength;

          source.vx += fx;
          source.vy += fy;
          target.vx -= fx;
          target.vy -= fy;
        });

        // Repulsion
        for (let i = 0; i < nextNodes.length; i++) {
          for (let j = i + 1; j < nextNodes.length; j++) {
            const ni = nextNodes[i];
            const nj = nextNodes[j];
            const dx = nj.x - ni.x;
            const dy = nj.y - ni.y;
            const dist = dx * dx + dy * dy || 1;
            if (dist < 40000) {
              const f = 20 / dist;
              ni.vx -= dx * f;
              ni.vy -= dy * f;
              nj.vx += dx * f;
              nj.vy += dy * f;
            }
          }
        }

        // Apply velocity & damping
        for (let n of nextNodes) {
          n.x += n.vx;
          n.y += n.vy;
          n.vx *= 0.9;
          n.vy *= 0.9;

          // Constraints
          n.x = Math.max(20, Math.min(dimensions.width - 20, n.x));
          n.y = Math.max(20, Math.min(dimensions.height - 20, n.y));
        }

        return nextNodes;
      });

      animationFrameId = requestAnimationFrame(tick);
    };

    animationFrameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animationFrameId);
  }, [links, dimensions]);

  const nodeColors = {
    agent: "#6d5efc",
    concept: "#2f7bff",
    risk: "#ef4444",
    opportunity: "#10b981",
  };

  return (
    <div ref={containerRef} className="relative h-full w-full overflow-hidden bg-black/40 rounded-3xl border border-white/10">
      <div className="absolute top-4 left-4 z-10 flex flex-col gap-1">
        <h3 className="text-xs font-bold uppercase tracking-wider text-white/50">Agent Interaction Graph</h3>
        <div className="flex items-center gap-3">
            <span className="flex items-center gap-1 text-[10px] text-white/70"><span className="h-2 w-2 rounded-full bg-[#6d5efc]" /> Agent</span>
            <span className="flex items-center gap-1 text-[10px] text-white/70"><span className="h-2 w-2 rounded-full bg-[#2f7bff]" /> Concept</span>
        </div>
      </div>
      
      <svg className="h-full w-full pointer-events-none">
        <g>
          {links.map((link, i) => {
            const s = nodes.find((n) => n.id === link.source);
            const t = nodes.find((n) => n.id === link.target);
            if (!s || !t) return null;
            return (
              <line
                key={`${link.source}-${link.target}-${i}`}
                x1={s.x}
                y1={s.y}
                x2={t.x}
                y2={t.y}
                stroke="white"
                strokeOpacity="0.1"
                strokeWidth="1"
              />
            );
          })}
        </g>
        <g>
          {nodes.map((node) => (
            <motion.g
              key={node.id}
              initial={{ scale: 0 }}
              animate={{ scale: 1, x: node.x, y: node.y }}
              transition={{ type: "spring", stiffness: 300, damping: 20 }}
            >
              <circle
                r={node.size / 2}
                fill={nodeColors[node.type] || "#fff"}
                className="drop-shadow-[0_0_8px_rgba(109,94,252,0.5)]"
              />
              <text
                dy={node.size + 2}
                textAnchor="middle"
                className="fill-white/80 text-[10px] font-medium pointer-events-none"
              >
                {node.label}
              </text>
            </motion.g>
          ))}
        </g>
      </svg>
    </div>
  );
}
