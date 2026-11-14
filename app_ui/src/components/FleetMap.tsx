import "leaflet/dist/leaflet.css";
import { latLngBounds, type LatLngBoundsExpression } from "leaflet";
import { useEffect, useMemo, useState } from "react";
import { CircleMarker, MapContainer, TileLayer, Tooltip, useMap } from "react-leaflet";
import { useNavigate } from "react-router-dom";
import type { RiskRow, Tier } from "../lib/api";
import { component, eur, farmLabel, pct } from "../lib/format";

export const TIER_FILL: Record<Tier, string> = {
  CRITICAL: "#FF3621", HIGH: "#FBB300", MEDIUM: "#618794", LOW: "#00A972", DOWN: "#A0AEC0",
};
const TIER_LABEL: Record<Tier, string> = { CRITICAL: "Critical", HIGH: "High", MEDIUM: "Medium", LOW: "Low", DOWN: "In repair" };
const ORDER: Tier[] = ["LOW", "DOWN", "MEDIUM", "HIGH", "CRITICAL"]; // draw risky turbines last (on top)
const RADIUS: Record<Tier, number> = { CRITICAL: 9, HIGH: 8, MEDIUM: 6, LOW: 5, DOWN: 5 };

interface FarmSummary { name: string; n: number; critical: number; high: number; bounds: LatLngBoundsExpression }

/** Keeps the Leaflet view in sync with React state: fit to a farm or the fleet, and resize when the panel expands. */
function ViewController({ target, expanded }: { target: LatLngBoundsExpression; expanded: boolean }) {
  const map = useMap();
  useEffect(() => {
    const t = setTimeout(() => {
      map.invalidateSize();
      map.flyToBounds(target, { padding: [36, 36], duration: 0.8, maxZoom: 13 });
    }, 60);
    return () => clearTimeout(t);
  }, [map, target, expanded]);
  return null;
}

export function FleetMap({ rows }: { rows: RiskRow[] }) {
  const nav = useNavigate();
  const [expanded, setExpanded] = useState(false);
  const [focus, setFocus] = useState<string>("fleet");

  const fleetBounds = useMemo(() => latLngBounds(rows.map((r) => [r.latitude, r.longitude] as [number, number])), [rows]);
  const farms = useMemo<FarmSummary[]>(() => {
    const by = new Map<string, RiskRow[]>();
    rows.forEach((r) => by.set(r.farm_name, [...(by.get(r.farm_name) ?? []), r]));
    return [...by.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([name, rs]) => ({
      name, n: rs.length,
      critical: rs.filter((r) => r.risk_tier === "CRITICAL").length,
      high: rs.filter((r) => r.risk_tier === "HIGH").length,
      bounds: latLngBounds(rs.map((r) => [r.latitude, r.longitude] as [number, number])),
    }));
  }, [rows]);
  const target = focus === "fleet" ? fleetBounds : farms.find((f) => f.name === focus)?.bounds ?? fleetBounds;
  const sorted = useMemo(() => [...rows].sort((a, b) => ORDER.indexOf(a.risk_tier) - ORDER.indexOf(b.risk_tier)), [rows]);

  useEffect(() => {
    if (!expanded) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setExpanded(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [expanded]);

  return (
    <figure className={`map${expanded ? " expanded" : ""}`} style={{ margin: 0 }}>
      {expanded && <div className="map-backdrop" onClick={() => setExpanded(false)} aria-hidden="true" />}
      <div className="map-frame">
        <div className="map-toolbar" role="group" aria-label="Map view">
          <button type="button" className="chip" aria-pressed={focus === "fleet"} onClick={() => setFocus("fleet")}>Fleet</button>
          {farms.map((f) => (
            <button key={f.name} type="button" className="chip" aria-pressed={focus === f.name} onClick={() => setFocus(f.name)}>
              {farmLabel(f.name)}
              {f.critical + f.high > 0 && <span className="chip-count" style={{ background: f.critical ? TIER_FILL.CRITICAL : TIER_FILL.HIGH }}>{f.critical + f.high}</span>}
            </button>
          ))}
        </div>

        <div className="map-canvas-wrap">
        <button type="button" className="map-expand" onClick={() => setExpanded((v) => !v)} aria-expanded={expanded}
                aria-label={expanded ? "Close the full-screen map" : "Expand the map"}>
          {expanded ? "Close ✕" : "Expand ⤢"}
        </button>

        <MapContainer bounds={fleetBounds} boundsOptions={{ padding: [36, 36] }} scrollWheelZoom={expanded} className="map-canvas"
                      aria-label="Map of the four wind farms with turbines coloured by risk tier">
          <TileLayer
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            maxZoom={19}
          />
          <ViewController target={target} expanded={expanded} />
          {sorted.map((r) => {
            const risky = r.risk_tier === "CRITICAL" || r.risk_tier === "HIGH";
            return (
              <CircleMarker key={r.turbine_id} center={[r.latitude, r.longitude]} radius={RADIUS[r.risk_tier]}
                            pathOptions={{ color: risky ? "#0B2026" : "#FFFFFF", weight: risky ? 2 : 1, fillColor: TIER_FILL[r.risk_tier], fillOpacity: 0.95 }}
                            className={r.risk_tier === "CRITICAL" ? "pulse" : undefined}
                            eventHandlers={{ click: () => nav(`/turbines/${r.turbine_id}`) }}>
                <Tooltip direction="top" offset={[0, -8]} opacity={1} className="turbine-tip">
                  <div className="tip-head">
                    <b className="mono">{r.turbine_id}</b>
                    <span className="tip-tier" style={{ background: TIER_FILL[r.risk_tier] }}>{TIER_LABEL[r.risk_tier]}</span>
                  </div>
                  <div className="tip-farm">{farmLabel(r.farm_name)} · {r.model} · {r.turbine_age_years} yrs</div>
                  <dl>
                    <dt>Failure risk, 14 days</dt><dd>{pct(r.failure_prob_14d, 1)}</dd>
                    <dt>Likely component</dt><dd>{component(r.likely_component)}</dd>
                    <dt>Avoidable if planned</dt><dd>{eur(r.avoidable_cost_if_caught_eur)}</dd>
                    <dt>Action</dt><dd>{r.recommended_window}</dd>
                  </dl>
                  {risky && <div className="tip-cta">Click to open the AI brief →</div>}
                </Tooltip>
              </CircleMarker>
            );
          })}
        </MapContainer>
        </div>

        <figcaption className="legend">
          {(["CRITICAL", "HIGH", "MEDIUM", "LOW", "DOWN"] as Tier[]).map((t) => (
            <span key={t}><i style={{ background: TIER_FILL[t] }} />{TIER_LABEL[t]}</span>
          ))}
          <span className="muted" style={{ marginLeft: "auto" }}>Hover a turbine for its status · click to open it</span>
        </figcaption>
      </div>
    </figure>
  );
}
