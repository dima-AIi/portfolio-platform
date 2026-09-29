import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { analyticsApi, type AnalyticsSummary } from "../../services/ownerData";
import { ErrorBanner } from "../ui/ErrorBanner";
import { plural } from "../../utils/plural";

const WINDOWS = [
  { days: 7, label: "7 дней" },
  { days: 30, label: "30 дней" },
  { days: 90, label: "90 дней" },
];

/**
 * Small inline bar chart — no chart library for four numbers a day.
 *
 * The series is a fixed trailing window, not the selected range, so the
 * caption states the real span instead of letting the number above it
 * ("N визитов за 30 дней") imply the chart covers those 30 days.
 */
function Sparkline({ points }: { points: { date: string; views: number }[] }) {
  const max = Math.max(...points.map((p) => p.views), 1);
  const days = points.length;
  return (
    <div className="spark-wrap">
      <div className="spark" role="img" aria-label={`Просмотры по дням за ${days} дней`}>
        {points.map((p) => (
          <span
            key={p.date}
            className="spark-bar"
            style={{ height: `${Math.max((p.views / max) * 100, 3)}%` }}
            title={`${p.date}: ${p.views}`}
          />
        ))}
      </div>
      <span className="spark-caption">последние {days} дней</span>
    </div>
  );
}

export function AnalyticsPanel() {
  const [days, setDays] = useState(30);
  const [data, setData] = useState<AnalyticsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  // Bumped to re-run the effect: the window switcher must stay usable so a
  // failed load can be retried or narrowed instead of leaving a dead panel.
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    analyticsApi
      .summary(days)
      .then((d) => {
        if (!cancelled) {
          setData(d);
          setError(null);
        }
      })
      .catch(() => {
        if (!cancelled) setError("Не удалось загрузить аналитику.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [days, attempt]);

  return (
    <section className="dash-section">
      <div className="dash-section-head">
        <h2 className="dash-section-title">Аналитика</h2>
        <div className="window-switch">
          {WINDOWS.map((w) => (
            <button
              key={w.days}
              type="button"
              className={`window-btn ${days === w.days ? "active" : ""}`}
              onClick={() => setDays(w.days)}
            >
              {w.label}
            </button>
          ))}
        </div>
      </div>

      {error ? (
        <div className="card card-pad">
          <ErrorBanner message={error} onRetry={() => setAttempt((n) => n + 1)} />
        </div>
      ) : loading && !data ? (
        <div className="card card-pad">
          <div className="spinner" />
        </div>
      ) : data && data.total_views === 0 ? (
        <div className="card card-pad muted">
          Пока нет данных — поделитесь ссылкой на портфолио, и здесь появятся источники
          переходов и просмотры по кейсам.
        </div>
      ) : data ? (
        <>
          <div className="card card-pad analytics-top">
            <div>
              <span className="stat-value">{data.window_views}</span>
              <span className="stat-label">
                {plural(data.window_views, "визит", "визита", "визитов")} за{" "}
                {data.window_days} дней
              </span>
            </div>
            <Sparkline points={data.daily} />
          </div>

          <div className="analytics-grid">
            <div className="card card-pad">
              <h3>Откуда приходят</h3>
              {data.sources.length === 0 ? (
                <p className="muted">Пока нет переходов извне.</p>
              ) : (
                <ul className="source-list">
                  {data.sources.map((s) => (
                    <li key={s.source}>
                      <span>{s.source}</span>
                      <span className="muted">{s.views}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="card card-pad">
              <h3>Какие кейсы смотрят</h3>
              {data.top_projects.length === 0 ? (
                <p className="muted">Кейсы ещё не открывали.</p>
              ) : (
                <ul className="source-list">
                  {data.top_projects.map((p) => (
                    <li key={p.id}>
                      <Link to={`/dashboard/projects/${p.id}`}>{p.title}</Link>
                      <span className="muted">{p.views}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}
