"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

function asString(v: unknown) {
  if (typeof v === "string") return v;
  if (typeof v === "number") return String(v);
  if (v && typeof v === "object") return JSON.stringify(v, null, 2);
  return "";
}

export function PredictionCard({
  title,
  subtitle,
  data,
}: {
  title: string;
  subtitle?: string;
  data: unknown;
}) {
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>{title}</CardTitle>
          {subtitle ? <CardDescription>{subtitle}</CardDescription> : null}
        </div>
      </CardHeader>
      <CardContent>
        <pre className="max-h-[520px] overflow-auto rounded-xl bg-black/30 p-3 text-xs text-white/75 ring-1 ring-white/10">
          {asString(data)}
        </pre>
      </CardContent>
    </Card>
  );
}

