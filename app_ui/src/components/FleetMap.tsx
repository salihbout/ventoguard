import { useNavigate } from "react-router-dom";
import type { RiskRow, Tier } from "../lib/api";
import { farmLabel } from "../lib/format";

// Equirectangular projection of Germany's bounding box; turbines are drawn at their real coordinates.
const BOUNDS = { lonMin: 5.6, lonMax: 15.2, latMin: 47.2, latMax: 55.1 };
const W = 520, H = 600;
const x = (lon: number) => ((lon - BOUNDS.lonMin) / (BOUNDS.lonMax - BOUNDS.lonMin)) * W;
const y = (lat: number) => ((BOUNDS.latMax - lat) / (BOUNDS.latMax - BOUNDS.latMin)) * H;

export const TIER_FILL: Record<Tier, string> = {
  CRITICAL: "#FF3621", HIGH: "#FBB300", MEDIUM: "#618794", LOW: "#00A972", DOWN: "#A0AEC0",
};
const ORDER: Tier[] = ["LOW", "DOWN", "MEDIUM", "HIGH", "CRITICAL"]; // draw risky turbines last (on top)

// Simplified outline of Germany (lon, lat) for orientation only.
const OUTLINE: [number, number][] = [
  [6.1, 50.8], [5.9, 51.8], [6.8, 52.1], [7.0, 53.3], [8.0, 53.6], [8.7, 53.9], [9.0, 54.8], [10.0, 54.8], [11.0, 54.0],
  [12.4, 54.4], [13.7, 54.5], [14.3, 53.9], [14.2, 53.0], [14.7, 52.1], [15.0, 51.1], [14.3, 50.9], [12.5, 50.3],
  [13.8, 48.8], [13.0, 47.6], [10.4, 47.4], [9.6, 47.6], [7.6, 47.6], [7.5, 48.6], [8.2, 49.0], [6.4, 49.5], [6.1, 50.8],
];

export function FleetMap({ rows }: { rows: RiskRow[] }) {
  const nav = useNavigate();
  const farms = Object.values(
    rows.reduce<Record<string, { name: string; lat: number; lon: number; n: number; atRisk: number }>>((acc, r) => {
      const f = (acc[r.farm_id] ??= { name: r.farm_name, lat: 0, lon: 0, n: 0, atRisk: 0 });
      f.lat += r.latitude; f.lon += r.longitude; f.n += 1;
      if (r.risk_tier === "CRITICAL" || r.risk_tier === "HIGH") f.atRisk += 1;
      return acc;
    }, {}),
  ).map((f) => ({ ...f, lat: f.lat / f.n, lon: f.lon / f.n }));
  const sorted = [...rows].sort((a, b) => ORDER.indexOf(a.risk_tier) - ORDER.indexOf(b.risk_tier));

  return (
    <figure className="map" style={{ margin: 0 }}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Map of the four wind farms with turbines coloured by risk tier">
        <path d={"M" + OUTLINE.map(([lo, la]) => `${x(lo).toFixed(1)},${y(la).toFixed(1)}`).join(" L") + " Z"}
              fill="#EEEDE9" stroke="#C4CCD6" strokeWidth={1} />
        {sorted.map((r) => {
          // spread each farm's turbines on a small grid around the farm centre so every turbine is visible
          const idx = Number(r.turbine_id.split("-T")[1]) - 1;
          const cx = x(r.longitude) + ((idx % 6) - 2.5) * 7, cy = y(r.latitude) + (Math.floor(idx / 6) - 2.5) * 7;
          const risky = r.risk_tier === "CRITICAL" || r.risk_tier === "HIGH";
          return (
            <circle key={r.turbine_id} cx={cx} cy={cy} r={risky ? 6 : 3.5} fill={TIER_FILL[r.risk_tier]}
                    stroke={risky ? "#0B2026" : "none"} strokeWidth={1} style={{ cursor: "pointer" }}
                    tabIndex={risky ? 0 : -1} onClick={() => nav(`/turbines/${r.turbine_id}`)}
                    onKeyDown={(e) => e.key === "Enter" && nav(`/turbines/${r.turbine_id}`)}>
              <title>{`${r.turbine_id} · ${r.risk_tier} · ${(r.failure_prob_14d * 100).toFixed(0)} % · ${r.likely_component.replace(/_/g, " ")}`}</title>
            </circle>
          );
        })}
        {farms.map((f) => (
          // eastern farms are labelled to the left so the text stays inside the map
          <g key={f.name} transform={`translate(${x(f.lon) + (f.lon > 11 ? -30 : 28)},${y(f.lat) - 18})`}
             textAnchor={f.lon > 11 ? "end" : "start"}>
            <text className="farm-label">{farmLabel(f.name)}</text>
            <text className="farm-sub" y={16}>{f.n} turbines · {f.atRisk} at risk</text>
          </g>
        ))}
      </svg>
      <figcaption className="legend">
        {(["CRITICAL", "HIGH", "MEDIUM", "LOW", "DOWN"] as Tier[]).map((t) => (
          <span key={t}><i style={{ background: TIER_FILL[t] }} />{t === "DOWN" ? "In repair" : t[0] + t.slice(1).toLowerCase()}</span>
        ))}
      </figcaption>
    </figure>
  );
}
