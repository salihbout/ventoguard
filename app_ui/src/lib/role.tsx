import { createContext, useContext, useState, type ReactNode } from "react";

/** Who is looking at the app. Each role gets its own home screen and navigation; every screen stays reachable by URL. */
export type Role = "executive" | "asset" | "operations";

export interface RoleDef { id: Role; label: string; who: string; home: string; nav: { to: string; label: string }[] }

export const ROLES: RoleDef[] = [
  { id: "executive", label: "Executive", who: "COO", home: "/executive",
    nav: [{ to: "/executive", label: "Overview" }, { to: "/ask", label: "Ask the fleet" }] },
  { id: "asset", label: "Asset management", who: "Head of Asset Management", home: "/assets",
    nav: [{ to: "/assets", label: "Asset performance" }, { to: "/", label: "Fleet risk" }, { to: "/work-orders", label: "Work orders" }, { to: "/ask", label: "Ask the fleet" }] },
  { id: "operations", label: "Operations", who: "Reliability lead · dispatcher", home: "/",
    nav: [{ to: "/", label: "Fleet risk" }, { to: "/work-orders", label: "Work orders" }, { to: "/ask", label: "Ask the fleet" }] },
];

const KEY = "vg.role";
const Ctx = createContext<{ role: RoleDef; setRole: (r: Role) => void }>({ role: ROLES[2], setRole: () => {} });

export function RoleProvider({ children }: { children: ReactNode }) {
  const [id, setId] = useState<Role>(() => (localStorage.getItem(KEY) as Role) || "operations");
  const role = ROLES.find((r) => r.id === id) ?? ROLES[2];
  const setRole = (r: Role) => { localStorage.setItem(KEY, r); setId(r); };
  return <Ctx.Provider value={{ role, setRole }}>{children}</Ctx.Provider>;
}

export const useRole = () => useContext(Ctx);
