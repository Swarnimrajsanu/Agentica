import type { ReactNode } from "react";
import { Sidebar } from "@/components/Sidebar";

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <div className="mx-auto flex max-w-[1400px] gap-4 md:gap-6">
        <Sidebar />
        <main className="flex-1 pb-10">
          {children}
        </main>
      </div>
    </div>
  );
}

