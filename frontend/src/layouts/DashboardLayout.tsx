import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";

const navItems = [
  { to: "/dashboard", label: "Обзор", end: true },
  { to: "/dashboard/profile", label: "Профиль" },
  { to: "/dashboard/projects", label: "Проекты" },
  { to: "/dashboard/portfolio", label: "Портфолио" },
  { to: "/dashboard/settings", label: "Настройки" },
];

export function DashboardLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="dashboard">
      <aside className="dashboard-sidebar">
        <div className="dashboard-brand">
          <NavLink to="/" className="brand-mark">
            PP
          </NavLink>
          <span>Portfolio Platform</span>
        </div>
        <nav className="dashboard-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `dashboard-nav-link ${isActive ? "active" : ""}`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="dashboard-sidebar-footer">
          {user && (
            <NavLink to={`/${user.username}`} className="public-link">
              Открыть публичную страницу ↗
            </NavLink>
          )}
          <button type="button" className="btn btn-ghost btn-sm" onClick={logout}>
            Выйти
          </button>
        </div>
      </aside>
      <main className="dashboard-main">
        <Outlet />
      </main>
    </div>
  );
}
