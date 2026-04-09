"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/cn";
import { 
  AlertCircle, 
  ChevronDown, 
  ChevronUp, 
  ShieldAlert, 
  ShieldCheck, 
  ArrowDownRight,
  EyeOff,
  Skull
} from "lucide-react";

interface Vulnerability {
  id: string;
  level: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  name: string;
  description: string;
  missedBy: string[];
  mitigation: string;
  details: string;
}

const vulnerabilities: Vulnerability[] = [
  {
    id: "v1",
    level: "CRITICAL",
    name: "Supply Chain Single Point of Failure",
    description: "The consensus relies heavily on a single raw material supplier in Southeast Asia without considering geopolitical risk or alternative sourcing for the AI chipset components.",
    missedBy: ["SupplyChainBot", "EconomistAgent"],
    mitigation: "Establish multi-region supplier redundancy and increase 6-month buffer stock for critical components.",
    details: "Analysis reveals a 35% probability of logistics disruption in the Malacca Strait which was entirely ignored by the simulation agents who assumed baseline efficiency."
  },
  {
    id: "v2",
    level: "HIGH",
    name: "Regulatory Timeline Underestimated",
    description: "Simulation assumes EU AI Act compliance in 4 months; actual historical average for similar scale certifications is 9-14 months.",
    missedBy: ["StrategyLead", "FounderAgent"],
    mitigation: "Adjust GTM strategy to prioritize 'Soft-Launch' in non-EU territories first.",
    details: "The current roadmap has a critical path dependency on the Certification body which currently has a 6-month backlog."
  },
  {
    id: "v3",
    level: "HIGH",
    name: "Competitive Response from Mamaearth",
    description: "Consensus assumes price leadership; Red Team predicts aggressive bundling and predatory pricing from established incumbents within 48 hours of launch.",
    missedBy: ["MarketAnalyst"],
    mitigation: "Front-load marketing budget for brand loyalty programs rather than pure performance ads.",
    details: "Mamaearth's historical response to niche competitors involves 40% discount bundling which would negate our projected 12% margin advantage."
  },
  {
    id: "v4",
    level: "MEDIUM",
    name: "Instagram Algorithm Dependency",
    description: "Marketing strategy assumes 3.2% organic reach; ignores potential algorithmic suppression of AI-generated content labels.",
    missedBy: ["SocialBot", "MarketingAgent"],
    mitigation: "Diversify to email marketing and community-led growth (Discord/Telegram).",
    details: "Meta's latest internal updates suggest a down-rank for 'AI-produced' watermarked content in the Explore feed."
  },
  {
    id: "v5",
    level: "LOW",
    name: "Currency Fluctuation Risk",
    description: "The model is pegged to USD; 5% volatility in local currency would lead to 2% bottom-line shrinkage.",
    missedBy: ["Everyone"],
    mitigation: "Implement standard hedging contracts for quarterly settlements.",
    details: "Standard macro-economic risk that was slightly overlooked but remains manageable."
  }
];

interface RedTeamReportProps {
  data?: any;
}

export function RedTeamReport({ data }: RedTeamReportProps) {
  const [expanded, setExpanded] = useState<string | null>(null);

  const reportData = data || {
      revised_confidence: 61,
      vulnerabilities: [
          {
            id: "v1",
            level: "CRITICAL",
            name: "Supply Chain Single Point of Failure",
            description: "The consensus relies heavily on a single raw material supplier in Southeast Asia without considering geopolitical risk or alternative sourcing for the AI chipset components.",
            missedBy: ["SupplyChainBot", "EconomistAgent"],
            mitigation: "Establish multi-region supplier redundancy and increase 6-month buffer stock for critical components.",
            details: "Analysis reveals a 35% probability of logistics disruption in the Malacca Strait which was entirely ignored by the simulation agents who assumed baseline efficiency."
          },
          {
            id: "v2",
            level: "HIGH",
            name: "Regulatory Timeline Underestimated",
            description: "Simulation assumes EU AI Act compliance in 4 months; actual historical average for similar scale certifications is 9-14 months.",
            missedBy: ["StrategyLead", "FounderAgent"],
            mitigation: "Adjust GTM strategy to prioritize 'Soft-Launch' in non-EU territories first.",
            details: "The current roadmap has a critical path dependency on the Certification body which currently has a 6-month backlog."
          }
      ],
      blind_spots: [
          "Long-tail tail-end risks (Black Swan events) were uniformly ignored by all agents.",
          "Psychological exhaustion of the customer support team in month 3.",
          "Environmental impact of chip waste during faulty production runs."
      ],
      worst_case: "A combined logistics strike and sudden regulatory pivot during the first 48 hours of launch triggers a 90% liquidity drain."
  };

  const vulnerabilities = reportData.vulnerabilities || [];

  const levelStyles = {
    CRITICAL: "bg-red-500/20 text-red-400 border-red-500/50",
    HIGH: "bg-orange-500/20 text-orange-400 border-orange-500/50",
    MEDIUM: "bg-yellow-500/20 text-yellow-400 border-yellow-500/50",
    LOW: "bg-gray-500/20 text-gray-400 border-gray-500/50",
  };

  return (
    <div className="space-y-6 text-white p-2">
      {/* Header */}
      <div className="glass rounded-3xl p-6 border border-red-500/20 bg-gradient-to-br from-red-500/5 to-transparent">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 rounded-full bg-red-500/20 flex items-center justify-center border border-red-500/40">
              <ShieldAlert className="text-red-500" size={24} />
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-tight flex items-center gap-2">
                RED TEAM REPORT <span className="text-[10px] bg-red-500 text-white px-2 py-0.5 rounded-full uppercase">Adversarial</span>
              </h2>
              <p className="text-sm text-white/50">Adversarial analysis of simulation consensus</p>
            </div>
          </div>
          <div className="text-right">
            <div className="flex items-center gap-2 text-red-400 font-mono font-bold text-lg">
              74% <ArrowDownRight size={16} /> {reportData.revised_confidence}%
            </div>
            <p className="text-[10px] text-white/30 uppercase tracking-widest">Revised Confidence</p>
          </div>
        </div>
      </div>

      {/* Vulnerabilities */}
      <div className="space-y-3">
        {vulnerabilities.map((v: any, i: number) => (
          <div 
            key={v.id || i}
            className="glass rounded-2xl border border-white/5 overflow-hidden transition-all hover:border-red-500/30"
          >
            <div 
              className="p-4 cursor-pointer flex items-start gap-4"
              onClick={() => setExpanded(expanded === (v.id || i) ? null : (v.id || i))}
            >
              <div className={cn("px-2 py-0.5 rounded text-[9px] font-bold border", levelStyles[v.level as keyof typeof levelStyles])}>
                {v.level}
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-bold text-white/90">{v.name}</h3>
                <p className="text-xs text-white/50 mt-1 line-clamp-2">{v.description}</p>
                
                <div className="mt-3 flex items-center gap-4 text-[10px]">
                  <div className="flex items-center gap-1 text-red-400/80">
                    <EyeOff size={10} />
                    <span>Missed by: {Array.isArray(v.missedBy) ? v.missedBy.join(", ") : v.missedBy}</span>
                  </div>
                  <div className="flex items-center gap-1 text-green-400/80">
                    <ShieldCheck size={10} />
                    <span>Mitigation ready</span>
                  </div>
                </div>
              </div>
              <div className="text-white/20">
                {expanded === (v.id || i) ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </div>
            </div>

            <AnimatePresence>
              {expanded === (v.id || i) && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="bg-white/5 border-t border-white/5"
                >
                  <div className="p-4 space-y-4">
                    <div className="space-y-1">
                      <h4 className="text-[10px] text-white/30 uppercase tracking-widest">Recommended Mitigation</h4>
                      <p className="text-xs text-green-300/90 leading-relaxed bg-green-500/10 p-2 rounded-lg border border-green-500/20">
                        {v.mitigation}
                      </p>
                    </div>
                    {v.details && (
                        <div className="space-y-1">
                        <h4 className="text-[10px] text-white/30 uppercase tracking-widest">Extended Analysis</h4>
                        <p className="text-xs text-white/70 leading-relaxed italic">
                            "{v.details}"
                        </p>
                        </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>

      {/* Blind Spots & Worst Case */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="glass rounded-3xl p-5 border border-white/5">
          <h3 className="text-xs font-bold text-white/40 uppercase tracking-widest mb-4 flex items-center gap-2">
            <EyeOff size={14} className="text-red-400" /> Systemic Blind Spots
          </h3>
          <ul className="space-y-3">
            {(reportData.blind_spots || []).map((spot: string, i: number) => (
              <li key={i} className="text-xs text-white/60 flex items-start gap-3">
                <span className="text-red-500/50 mt-1">•</span>
                {spot}
              </li>
            ))}
          </ul>
        </div>

        <div className="glass rounded-3xl p-5 border border-red-500/30 bg-red-500/5">
          <h3 className="text-xs font-bold text-red-400 uppercase tracking-widest mb-4 flex items-center gap-2">
            <Skull size={14} /> Worst Case Scenario
          </h3>
          <p className="text-xs text-white/70 leading-relaxed">
            {reportData.worst_case}
          </p>
          <div className="mt-4 pt-4 border-t border-red-500/20 text-[10px] text-red-400/60 font-mono italic">
            IMPACT MAP: CRITICAL / RECOVERY: LIKELY IMPOSSIBLE
          </div>
        </div>
      </div>
    </div>
  );
}
