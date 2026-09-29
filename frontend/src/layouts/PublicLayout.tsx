import { Link, Outlet } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";

export function PublicLayout() {
  const { user } = useAuth();

  return (
    <div className="public-layout">
      <header className="public-header">
        <div className="container public-header-inner">
          <Link to="/" className="brand-mark" aria-label="На главную">
            PP
          </Link>
          <nav className="public-header-nav">
            {/* An owner previewing their own page should see the way back to
                the dashboard, not a second "Создать портфолио" call to action. */}
            {user ? (
              <>
                <Link to="/dashboard" className="btn btn-ghost btn-sm">
                  В кабинет
                </Link>
                <span className="public-header-user">@{user.username}</span>
              </>
            ) : (
              <>
                <Link to="/login" className="btn btn-ghost btn-sm">
                  Войти
                </Link>
                <Link to="/register" className="btn btn-primary btn-sm">
                  Создать портфолио
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>
      <Outlet />
      <footer className="public-footer">
        <div className="container">
          <span>Portfolio Platform — покажите свои реальные работы.</span>
        </div>
      </footer>
    </div>
  );
}
