import type { Tier } from "../lib/api";

const LABEL: Record<Tier, string> = { CRITICAL: "Critical", HIGH: "High", MEDIUM: "Medium", LOW: "Low", DOWN: "In repair" };

export function RiskBadge({ tier }: { tier: Tier }) {
  return <span className={`tier tier-${tier}`}>{LABEL[tier] ?? tier}</span>;
}

export function ProbBar({ p, tier }: { p: number; tier: Tier }) {
  return (
    <div className="prob" aria-label={`Failure probability ${(p * 100).toFixed(0)} percent`}>
      <span className="mono">{(p * 100).toFixed(1)} %</span>
      <div className="prob-track"><div className={`prob-fill ${tier}`} style={{ width: `${Math.max(2, p * 100)}%` }} /></div>
    </div>
  );
}
