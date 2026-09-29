COMMON_PASSWORDS = frozenset({
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
    "asdfghjkl", "zxcvbnm123", "1234abcd",
})


def validate_password_strength(value: str) -> str:
    """Reject trivially weak passwords. Raises ValueError with a user-facing
    Russian message (surfaced through the API validation handler)."""
    if value.lower() in COMMON_PASSWORDS:
        raise ValueError("Этот пароль слишком распространён — выберите другой.")
    classes = 0
    if any(c.islower() for c in value):
        classes += 1
    if any(c.isupper() for c in value):
        classes += 1
    if any(c.isdigit() for c in value):
        classes += 1
    if any(not c.isalnum() for c in value):
        classes += 1
    if classes < 2:
        raise ValueError("Пароль слишком простой: добавьте цифры или спецсимволы.")
    return value


# bcrypt hashes at most 72 bytes and raises ValueError past that. Silently
# truncating would make two passwords sharing a 72-byte prefix equivalent, so
# the limit is enforced as a validation error instead.
BCRYPT_MAX_BYTES = 72


def validate_password_length(value: str) -> str:
    if len(value.encode("utf-8")) > BCRYPT_MAX_BYTES:
        raise ValueError(
            f"Пароль слишком длинный: максимум {BCRYPT_MAX_BYTES} байт."
        )
    return value
