import { useQuery } from "@tanstack/react-query";
import { NavLink, Route, Routes } from "react-router-dom";
import { api } from "./lib/api";
import { AskPage } from "./pages/AskPage";
import { FleetPage } from "./pages/FleetPage";
import { TurbinePage } from "./pages/TurbinePage";
import { WorkOrdersPage } from "./pages/WorkOrdersPage";

export function App() {
  const kpis = useQuery({ queryKey: ["kpis"], queryFn: api.kpis });
  return (
    <>
      <header className="shell-header">
        <a className="wordmark" href="/">VentoGuard<span>Drivetrain reliability</span></a>
        <nav className="nav" aria-label="Main">
          <NavLink to="/" end>Fleet risk</NavLink>
          <NavLink to="/work-orders">Work orders</NavLink>
          <NavLink to="/ask">Ask the fleet</NavLink>
        </nav>
        {kpis.data && (
          <span className="shell-meta">
            Scored <span className="mono">{kpis.data.score_date}</span> · model <span className="mono">turbine_failure_risk v{kpis.data.model_version}</span> · served from Lakebase
          </span>
        )}
      </header>
      <Routes>
        <Route path="/" element={<FleetPage />} />
        <Route path="/turbines/:id" element={<TurbinePage />} />
        <Route path="/work-orders" element={<WorkOrdersPage />} />
        <Route path="/ask" element={<AskPage />} />
      </Routes>
    </>
  );
}
