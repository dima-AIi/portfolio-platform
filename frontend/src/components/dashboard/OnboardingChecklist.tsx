import { Link } from "react-router-dom";

import type { Profile, Project } from "../../types";

interface OnboardingChecklistProps {
  profile: Profile;
  projects: Project[];
}

/**
 * Guides a new account from "signed up" to "page worth sharing".
 *
 * Deliberately a checklist rather than a wizard: it names what is still
 * missing and links straight to it, and it disappears once the page is
 * actually in decent shape. Every item is optional except the first
 * project — an unfinished profile is still better than none.
 */
export function OnboardingChecklist({ profile, projects }: OnboardingChecklistProps) {
  const published = projects.filter((p) => p.status === "PUBLISHED");

  const steps = [
    {
      done: Boolean(profile.display_name && profile.headline),
      title: "Заполните профиль",
      hint: "Имя и специализация — их видно первыми.",
      to: "/dashboard/profile",
      cta: "Заполнить",
    },
    {
      done: Boolean(profile.bio),
      title: "Напишите пару слов о себе",
      hint: "Короткий абзац помогает понять, чем вы занимаетесь.",
      to: "/dashboard/profile",
      cta: "Добавить",
    },
    {
      done: projects.length > 0,
      title: "Добавьте первый проект",
      hint: "Опишите задачу, решение и результат — это и есть портфолио.",
      to: projects.length ? "/dashboard/projects" : "/dashboard/projects/new",
      cta: projects.length ? "Открыть проекты" : "Создать проект",
    },
    {
      done: published.length > 0,
      title: "Опубликуйте проект",
      hint: "Черновик виден только вам — опубликованный попадёт на страницу.",
      to: "/dashboard/projects",
      cta: "Опубликовать",
    },
  ];

  const doneCount = steps.filter((s) => s.done).length;
  // Once everything is in place the checklist is noise; the stats below
  // already show the state of the portfolio.
  if (doneCount === steps.length) return null;

  return (
    <section className="card card-pad onboarding">
      <div className="onboarding-head">
        <div>
          <h2>Портфолио почти готово</h2>
          <p className="muted">
            Осталось {steps.length - doneCount}{" "}
            {steps.length - doneCount === 1 ? "шаг" : "шага"} из {steps.length}. Можно
            пропустить и вернуться позже.
          </p>
        </div>
        <span className="onboarding-count">
          {doneCount}/{steps.length}
        </span>
      </div>

      <div
        className="onboarding-bar"
        role="progressbar"
        aria-valuenow={doneCount}
        aria-valuemin={0}
        aria-valuemax={steps.length}
        aria-label="Заполненность портфолио"
      >
        <span style={{ width: `${(doneCount / steps.length) * 100}%` }} />
      </div>

      <ol className="onboarding-steps">
        {steps.map((step) => (
          <li key={step.title} className={step.done ? "done" : ""}>
            <span className="onboarding-check" aria-hidden="true">
              {step.done ? "✓" : "○"}
            </span>
            <div className="onboarding-step-main">
              <strong>{step.title}</strong>
              {!step.done && <span className="muted">{step.hint}</span>}
            </div>
            {!step.done && (
              <Link to={step.to} className="btn btn-secondary btn-sm">
                {step.cta}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}
