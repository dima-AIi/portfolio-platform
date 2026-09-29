const COMMON_PASSWORDS = new Set([
  "password", "password1", "password12", "password123", "password!",
  "passw0rd", "p@ssword", "p@ssw0rd", "passwort",
  "12345678", "123456789", "1234567890", "12345678901",
  "11111111", "00000000", "12121212", "123123123", "000000000",
  "qwerty", "qwerty123", "qwertyuiop", "qwerty12", "qwe12345",
  "1q2w3e4r", "1qaz2wsx", "qazwsx123", "a1b2c3d4", "abcd1234",
  "abc123456", "abcd12345", "123qwe123", "1234qwer",
  "iloveyou", "iloveyou1", "letmein", "letmein123", "welcome",
  "welcome1", "welcome123", "admin123", "admin1234", "root1234",
  "toor123", "user1234", "guest123", "default", "test1234",
  "testing1", "changeme", "secret123", "master123", "monkey123",
  "dragon123", "superman", "batman123", "trustno1", "starwars",
  "matrix123", "football", "baseball", "sunshine", "princess",
  "jordan23", "hunter123", "whatever", "computer", "internet",
  "samantha", "alexander", "jennifer", "michelle", "geronimo",
  "1234qwer", "asdfghjkl", "zxcvbnm123", "1234abcd",
]);

/** bcrypt hashes at most 72 bytes; the API enforces the same ceiling. */
export const PASSWORD_MAX_BYTES = 72;

export interface StrengthInfo {
  score: 0 | 1 | 2 | 3 | 4;
  label: string;
  ok: boolean;
  hint?: string;
}

function charClasses(pw: string): number {
  let classes = 0;
  if (/[a-zа-яё]/.test(pw)) classes += 1;
  if (/[A-ZА-ЯЁ]/.test(pw)) classes += 1;
  if (/\d/.test(pw)) classes += 1;
  if (/[^a-zA-Z0-9а-яёА-ЯЁ]/.test(pw)) classes += 1;
  return classes;
}

export function scorePassword(pw: string): StrengthInfo {
  if (!pw) return { score: 0, label: "", ok: false };
  if (pw.length < 8)
    return { score: 0, label: "Слабый", ok: false, hint: "Минимум 8 символов." };
  // bcrypt hashes at most 72 bytes and the API rejects more, so flag it here
  // rather than letting the user fill a long password only to get a 422.
  if (new TextEncoder().encode(pw).length > PASSWORD_MAX_BYTES)
    return {
      score: 0,
      label: "Слишком длинный",
      ok: false,
      hint: `Пароль не может быть длиннее ${PASSWORD_MAX_BYTES} байт.`,
    };
  if (COMMON_PASSWORDS.has(pw.toLowerCase()))
    return { score: 0, label: "Слабый", ok: false, hint: "Слишком распространённый пароль." };

  const classes = charClasses(pw);
  if (classes < 2)
    return {
      score: 1,
      label: "Слабый",
      ok: false,
      hint: "Добавьте цифры или спецсимволы.",
    };

  let score = 2;
  if (pw.length >= 12) score += 1;
  if (classes >= 3) score += 1;
  if (score > 4) score = 4;

  const labels: Record<number, string> = { 2: "Средний", 3: "Хороший", 4: "Надёжный" };
  return { score: score as StrengthInfo["score"], label: labels[score], ok: true };
}
