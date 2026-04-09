"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";
import {
  LayoutDashboard,
  Sparkles,
  MessageSquareText,
  LineChart,
  GitCompare,
  MessagesSquare,
  ShieldAlert,
} from "lucide-react";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/new", label: "New Simulation", icon: Sparkles },
  { href: "/simulation", label: "Simulation", icon: MessageSquareText },
  { href: "/redteam", label: "Red Team", icon: ShieldAlert },
  { href: "/predictions", label: "Predictions", icon: LineChart },
  { href: "/butterfly", label: "Butterfly Effect", icon: GitCompare },
  { href: "/agent-chat", label: "Agent Chat", icon: MessagesSquare },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex md:w-72 md:flex-col md:gap-3 md:p-4">
      <div className="glass rounded-2xl px-4 py-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold tracking-wide text-white/90">Agentica</div>
            <div className="text-xs text-white/50">Multi-agent simulation</div>
          </div>
          <div className="h-9 w-9 rounded-xl bg-linear-to-br from-(--accent) to-(--accent-2)" />
        </div>
      </div>

      <nav className="glass rounded-2xl p-2">
        {nav.map((item) => {
          const active = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2 text-sm text-white/70 transition hover:bg-white/5 hover:text-white",
                active && "bg-white/8 text-white ring-1 ring-white/10",
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

