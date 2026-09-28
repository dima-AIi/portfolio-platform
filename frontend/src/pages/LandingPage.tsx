import { Link } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";
import { useSeo } from "../hooks/useSeo";

/** Screenshots of the showcase portfolio, served from /demo/elora. */
const SHOWCASE_SHOTS = [
  { src: "/demo/elora/og-cover.jpg", alt: "Обложка кейса ELORA" },
  { src: "/demo/elora/hero.jpg", alt: "Главная страница ELORA" },
  { src: "/demo/elora/manicure-01.jpg", alt: "Галерея работ ELORA" },
];

const STEPS = [
  {
    title: "Заведите аккаунт",
    text: "Логин по email — и вы сразу в личном кабинете. Никаких лишних полей.",
  },
  {
    title: "Соберите кейсы",
    text: "Проект = проблема, решение, результат и стек. Так это читают клиент и рекрутер.",
  },
  {
    title: "Поделитесь ссылкой",
    text: "Публичный адрес /ваше_имя. Отправляйте его вместо папки с файлами.",
  },
];

export function LandingPage() {
  const { user } = useAuth();
  useSeo({
    title: "Portfolio Platform — покажите реальные работы",
    description:
      "Создайте профессиональное портфолио с реальными проектами: Проблема, Решение, Результат, Технологии. Одна ссылка для работодателей и клиентов.",
    canonicalPath: "/",
  });

  return (
    <div className="landing">
      <header className="landing-header">
        <div className="container landing-header-inner">
          <Link to="/" className="brand-mark">
            PP
          </Link>
          <nav className="landing-nav">
            {user ? (
              <Link to="/dashboard" className="btn btn-primary btn-sm">
                В личный кабинет
              </Link>
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

      <section className="landing-hero">
        <div className="container">
          <h1>
            Покажите <span className="accent">реальные работы</span>,<br />
            а не просто слова о себе.
          </h1>
          <p className="landing-lead">
            Portfolio Platform превращает ваши проекты в профессиональные кейсы —
            Проблема, Решение, Результат, Технологии — и даёт одну публичную ссылку
            для работодателей и клиентов.
          </p>
          <div className="landing-cta">
            <Link to={user ? "/dashboard" : "/register"} className="btn btn-primary btn-lg">
              Создать портфолио — бесплатно
            </Link>
            <span className="landing-cta-note">Без карты. Готово за несколько минут.</span>
          </div>
        </div>
      </section>

      <section className="landing-showcase" id="showcase">
        <div className="container">
          <p className="landing-eyebrow">Живое портфолио</p>
          <h2 className="landing-showcase-title">
            Вот как это выглядит на настоящем проекте
          </h2>
          <p className="landing-showcase-lead">
            Ниже — реальное портфолио на этой платформе. Кейс собран по формуле
            «проблема → решение → результат», со скриншотами и стеком. Откройте
            ссылку и посмотрите, как это читает клиент или рекрутер.
          </p>

          <div className="showcase-window">
            <div className="showcase-window-bar">
              <span className="showcase-window-dots" aria-hidden="true">
                <i />
                <i />
                <i />
              </span>
              <Link to="/demo" className="showcase-window-url">
                /demo
              </Link>
            </div>

            <div className="showcase-window-body">
              <div className="showcase-profile">
                <div className="showcase-avatar">Д</div>
                <div>
                  <strong>Дмитрий К.</strong>
                  <span>Full-Stack разработчик</span>
                </div>
                <div className="tech-row showcase-techs">
                  <span className="badge badge-tech">C#</span>
                  <span className="badge badge-tech">ASP.NET Core</span>
                  <span className="badge badge-tech">PostgreSQL</span>
                  <span className="badge badge-tech">PWA</span>
                </div>
              </div>

              <div className="showcase-shots">
                {SHOWCASE_SHOTS.map((shot) => (
                  <figure key={shot.src} className="showcase-shot">
                    <img src={shot.src} alt={shot.alt} loading="lazy" />
                    <figcaption>{shot.alt}</figcaption>
                  </figure>
                ))}
              </div>

              <div className="showcase-case">
                <h3>ELORA — онлайн-запись в студию красоты</h3>
                <p>
                  24 услуги, запись в 8 шагов и серверный контроль пересечений слотов.
                  Полный кейс — с проблемой, решением и результатом.
                </p>
                <Link to="/demo" className="btn btn-primary">
                  Открыть портфолио →
                </Link>
              </div>
            </div>
          </div>

          <p className="showcase-note">
            Это демонстрационный аккаунт. Зарегистрируйтесь — и ваше портфолио
            будет выглядеть так же, только с вашими проектами.
          </p>
        </div>
      </section>

      <section className="landing-steps">
        <div className="container">
          <h2>Три шага до публичной ссылки</h2>
          <div className="steps-grid">
            {STEPS.map((step, index) => (
              <div key={step.title} className="card card-pad step-card">
                <span className="step-number">{index + 1}</span>
                <h3>{step.title}</h3>
                <p>{step.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="landing-features">
        <div className="container">
          <h2>Почему кейсы работают лучше списка ссылок</h2>
          <div className="feature-grid">
            <div className="card card-pad feature-card">
              <h3>Структура, которая продаёт</h3>
              <p>
                Каждый проект отвечает на вопросы, которые реально задаёт клиент: какая
                была проблема, что вы сделали и к чему это привело.
              </p>
            </div>
            <div className="card card-pad feature-card">
              <h3>Одна ссылка на всё</h3>
              <p>
                Ваше портфолио живёт по адресу /yourname — отправляйте его вместо
                скриншотов и репозиториев, разбросанных по чатам.
              </p>
            </div>
            <div className="card card-pad feature-card">
              <h3>Проекты — на первом месте</h3>
              <p>
                Работы — главный герой. Без десяти страниц «обо мне»: посетитель сразу
                видит проекты, технологии и результаты.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-cta-final">
        <div className="container">
          <h2>Готовы показать, что умеете?</h2>
          <Link to={user ? "/dashboard" : "/register"} className="btn btn-primary btn-lg">
            {user ? "Открыть личный кабинет" : "Создать портфолио"}
          </Link>
        </div>
      </section>

      <footer className="public-footer">
        <div className="container">
          <span>Portfolio Platform — покажите свои реальные работы.</span>
        </div>
      </footer>
    </div>
  );
}
