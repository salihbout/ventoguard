import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TrendDay } from "../lib/api";

export interface Series { key: keyof TrendDay; label: string; color: string; axis?: "left" | "right" }

const axisStyle = { fontSize: 12, fill: "#4A5568", fontFamily: "DM Sans" };

export function TrendChart({ data, series, unitLeft, unitRight }: { data: TrendDay[]; series: Series[]; unitLeft: string; unitRight?: string }) {
  const rows = data.map((d) => ({ ...d, day: d.reading_date.slice(5) }));
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={rows} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="#EEEDE9" vertical={false} />
        <XAxis dataKey="day" tick={axisStyle} tickLine={false} axisLine={{ stroke: "#C4CCD6" }} minTickGap={24} />
        <YAxis yAxisId="left" tick={axisStyle} tickLine={false} axisLine={false} width={44} domain={["auto", "auto"]}
               label={{ value: unitLeft, angle: -90, position: "insideLeft", style: axisStyle }} />
        {unitRight && (
          <YAxis yAxisId="right" orientation="right" tick={axisStyle} tickLine={false} axisLine={false} width={44} domain={["auto", "auto"]}
                 label={{ value: unitRight, angle: 90, position: "insideRight", style: axisStyle }} />
        )}
        <Tooltip contentStyle={{ fontFamily: "DM Sans", fontSize: 13, borderRadius: 8, border: "1px solid #C4CCD6" }}
                 formatter={(v: number) => (typeof v === "number" ? v.toFixed(2) : v)} />
        <Legend wrapperStyle={{ fontSize: 13, fontFamily: "DM Sans" }} iconType="plainline" />
        {series.map((s) => (
          <Line key={String(s.key)} yAxisId={s.axis ?? "left"} type="monotone" dataKey={s.key as string} name={s.label}
                stroke={s.color} strokeWidth={2} dot={false} isAnimationActive={false} connectNulls />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
