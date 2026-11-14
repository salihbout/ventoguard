import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { NavLink, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { AerionLogo } from "./components/AerionLogo";
import { api } from "./lib/api";
import { ROLES, useRole, type Role } from "./lib/role";
import { AskPage } from "./pages/AskPage";
import { AssetsPage } from "./pages/AssetsPage";
import { ExecutivePage } from "./pages/ExecutivePage";
import { FleetPage } from "./pages/FleetPage";
import { TurbinePage } from "./pages/TurbinePage";
import { WorkOrdersPage } from "./pages/WorkOrdersPage";

export function App() {
  const kpis = useQuery({ queryKey: ["kpis"], queryFn: api.kpis });
  const { role, setRole } = useRole();
  const nav = useNavigate();
  const switchTo = (r: Role) => { setRole(r); nav(ROLES.find((x) => x.id === r)!.home); };
  const { pathname } = useLocation();
  // Deep links to a role's home screen (e.g. /executive) switch the view to that role.
  useEffect(() => {
    const owner = ROLES.find((r) => r.home === pathname && r.home !== "/");
    if (owner && owner.id !== role.id) setRole(owner.id);
  }, [pathname]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <>
      <header className="shell-header">
        <AerionLogo />
        <span className="brand-divider" aria-hidden="true" />
        <a className="wordmark" href={role.home}>VentoGuard<span>Drivetrain reliability</span></a>
        <nav className="nav" aria-label="Main">
          {role.nav.map((n) => <NavLink key={n.to} to={n.to} end={n.to === "/"}>{n.label}</NavLink>)}
        </nav>
        <div className="role-switch" role="group" aria-label="View as">
          <span className="role-label">View as</span>
          {ROLES.map((r) => (
            <button key={r.id} type="button" aria-pressed={r.id === role.id} title={r.who} onClick={() => switchTo(r.id)}>{r.label}</button>
          ))}
        </div>
      </header>
      {kpis.data && (
        <div className="shell-meta-bar">
          Viewing as <b>{role.who}</b> · scored <span className="mono">{kpis.data.score_date}</span> · model{" "}
          <span className="mono">turbine_failure_risk v{kpis.data.model_version}</span> · served from Lakebase
        </div>
      )}
      <Routes>
        <Route path="/" element={<FleetPage />} />
        <Route path="/executive" element={<ExecutivePage />} />
        <Route path="/assets" element={<AssetsPage />} />
        <Route path="/turbines/:id" element={<TurbinePage />} />
        <Route path="/work-orders" element={<WorkOrdersPage />} />
        <Route path="/ask" element={<AskPage />} />
      </Routes>
    </>
  );
}
