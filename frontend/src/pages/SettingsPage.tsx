import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { ConfirmDialog } from "../components/ui/ConfirmDialog";
import { Button } from "../components/ui/Button";
import { Field, Input } from "../components/ui/Field";
import { PasswordInput } from "../components/ui/PasswordInput";
import { PasswordStrength } from "../components/ui/PasswordStrength";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../hooks/useToast";
import { ApiError } from "../services/api";
import { authApi } from "../services/auth";
import { exportApi } from "../services/ownerData";
import { scorePassword } from "../utils/passwordStrength";

export function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const { showSuccess, showError, toastNode } = useToast();
  const navigate = useNavigate();

  // Password
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [pwErrors, setPwErrors] = useState<Record<string, string>>({});
  const [savingPw, setSavingPw] = useState(false);

  // Email
  const [email, setEmail] = useState(user?.email ?? "");
  const [emailPassword, setEmailPassword] = useState("");
  const [emailErrors, setEmailErrors] = useState<Record<string, string>>({});
  const [savingEmail, setSavingEmail] = useState(false);

  // Danger zone
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const handleSubmitPassword = async (e: FormEvent) => {
    e.preventDefault();
    const errs: Record<string, string> = {};
    if (!current) errs.current = "Введите текущий пароль.";
    if (next.length < 8) {
      errs.next = "Новый пароль должен быть не короче 8 символов.";
    } else if (!scorePassword(next).ok) {
      errs.next = scorePassword(next).hint ?? "Пароль слишком простой.";
    }
    if (next !== confirm) errs.confirm = "Пароли не совпадают.";
    setPwErrors(errs);
    if (Object.keys(errs).length > 0) return;

    setSavingPw(true);
    try {
      await authApi.changePassword(current, next);
      setCurrent("");
      setNext("");
      setConfirm("");
      showSuccess("Пароль изменён");
    } catch (err) {
      if (err instanceof ApiError && err.code === "INVALID_CREDENTIALS") {
        setPwErrors({ current: "Текущий пароль указан неверно." });
      } else {
        showError(err instanceof ApiError ? err.message : "Не удалось изменить пароль.");
      }
    } finally {
      setSavingPw(false);
    }
  };

  const handleSubmitEmail = async (e: FormEvent) => {
    e.preventDefault();
    const errs: Record<string, string> = {};
    if (!/^\S+@\S+\.\S+$/.test(email)) errs.email = "Введите корректный email.";
    if (!emailPassword) errs.password = "Введите пароль для подтверждения.";
    setEmailErrors(errs);
    if (Object.keys(errs).length > 0) return;

    setSavingEmail(true);
    try {
      await authApi.changeEmail(email, emailPassword);
      await refreshUser();
      setEmailPassword("");
      showSuccess("Email обновлён");
    } catch (err) {
      if (err instanceof ApiError && err.code === "INVALID_CREDENTIALS") {
        setEmailErrors({ password: "Пароль указан неверно." });
      } else if (err instanceof ApiError && err.code === "EMAIL_ALREADY_EXISTS") {
        setEmailErrors({ email: "Этот email уже занят." });
      } else {
        showError(err instanceof ApiError ? err.message : "Не удалось изменить email.");
      }
    } finally {
      setSavingEmail(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleting) return;
    if (deletePassword.length < 8) {
      setDeleteError("Введите пароль (минимум 8 символов).");
      return;
    }
    setDeleting(true);
    try {
      await authApi.deleteAccount(deletePassword);
      // The account is gone, so its session cookie is meaningless. Ending the
      // session clears it server-side, and the reload drops the in-memory user.
      await authApi.logout();
      navigate("/", { replace: true });
      window.location.reload();
    } catch (err) {
      if (err instanceof ApiError && err.code === "INVALID_CREDENTIALS") {
        setDeleteError("Пароль указан неверно.");
      } else {
        setDeleteError("Не удалось удалить аккаунт.");
      }
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">Настройки</h1>
      <p className="page-subtitle">Безопасность вашего аккаунта.</p>

      <form onSubmit={handleSubmitPassword} noValidate className="card card-pad settings-card">
        <h3>Смена пароля</h3>
        <Field label="Текущий пароль" error={pwErrors.current}>
          <PasswordInput
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            autoComplete="current-password"
            invalid={!!pwErrors.current}
          />
        </Field>
        <div className="form-grid">
          <Field label="Новый пароль" error={pwErrors.next}>
            <div>
              <PasswordInput
                value={next}
                onChange={(e) => setNext(e.target.value)}
                placeholder="Минимум 8 символов"
                autoComplete="new-password"
                invalid={!!pwErrors.next}
              />
              <PasswordStrength password={next} />
            </div>
          </Field>
          <Field label="Повторите новый пароль" error={pwErrors.confirm}>
            <PasswordInput
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              autoComplete="new-password"
              invalid={!!pwErrors.confirm}
            />
          </Field>
        </div>
        <div className="form-actions">
          <Button type="submit" disabled={savingPw}>
            {savingPw ? "Сохраняем…" : "Изменить пароль"}
          </Button>
        </div>
      </form>

      <form onSubmit={handleSubmitEmail} noValidate className="card card-pad settings-card">
        <h3>Смена email</h3>
        <div className="form-grid">
          <Field label="Новый email" error={emailErrors.email}>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              invalid={!!emailErrors.email}
            />
          </Field>
          <Field label="Текущий пароль" error={emailErrors.password}>
            <PasswordInput
              value={emailPassword}
              onChange={(e) => setEmailPassword(e.target.value)}
              autoComplete="current-password"
              invalid={!!emailErrors.password}
            />
          </Field>
        </div>
        <div className="form-actions">
          <Button type="submit" variant="secondary" disabled={savingEmail}>
            {savingEmail ? "Сохраняем…" : "Изменить email"}
          </Button>
        </div>
      </form>

      <div className="card card-pad settings-card export-card">
        <h3>Скачать свои данные</h3>
        <p className="muted">
          Один файл со всем: профиль, проекты, технологии и ссылки на изображения.
          Храните копию — она останется с вами, даже если аккаунт будет удалён.
        </p>
        <Button variant="secondary" onClick={() => exportApi.download()}>
          Скачать JSON
        </Button>
      </div>

      <div className="card card-pad settings-card danger-zone">
        <h3>Удаление аккаунта</h3>
        <p className="muted">
          Аккаунт, профиль и все проекты (включая опубликованные) будут удалены
          безвозвратно. Это действие нельзя отменить.
        </p>
        <Button variant="danger" onClick={() => setDeleteOpen(true)}>
          Удалить аккаунт
        </Button>
      </div>

      <ConfirmDialog
        open={deleteOpen}
        title="Удалить аккаунт?"
        confirmLabel="Да, удалить всё"
        description="Все ваши проекты и данные будут удалены навсегда. Для подтверждения введите пароль в поле ниже."
        onCancel={() => {
          setDeleteOpen(false);
          setDeletePassword("");
          setDeleteError(null);
        }}
        onConfirm={() => void handleDeleteAccount()}
      >
        <Field label="Подтвердите паролем" error={deleteError ?? undefined}>
          <PasswordInput
            value={deletePassword}
            onChange={(e) => setDeletePassword(e.target.value)}
            autoComplete="current-password"
            invalid={!!deleteError}
          />
        </Field>
      </ConfirmDialog>

      {toastNode}
    </div>
  );
}
