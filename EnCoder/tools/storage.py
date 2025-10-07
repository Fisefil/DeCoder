import string
from typing import List
import mysql.connector

# --- Конфигурация базы ---
DB_CONFIG = {
    "host": "localhost",
    "user": "Fisefil",
    "password": "2Hhh4hh4;",
    "database": "DBEnCoder",
    "port": 3305
}

# --- Подключение ---
def get_conn():
    return mysql.connector.connect(**DB_CONFIG)

# --- Генерация следующего кода ---
def next_code(code: str) -> str:
    letters = string.ascii_uppercase
    code_list = list(code)
    i = len(code_list) - 1
    while i >= 0:
        idx = letters.index(code_list[i])
        if idx < len(letters) - 1:
            code_list[i] = letters[idx + 1]
            break
        else:
            code_list[i] = 'A'
            i -= 1
    return ''.join(code_list)

# --- Инициализация таблицы ---
def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            name TEXT,
            code VARCHAR(10) UNIQUE,
            username TEXT,
            chat_mode BOOLEAN DEFAULT FALSE,
            is_admin BOOLEAN DEFAULT FALSE,
            points INT DEFAULT 0,
            is_muted BOOLEAN DEFAULT FALSE,
            is_banned BOOLEAN DEFAULT FALSE,
            messages INT DEFAULT 0
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

# --- Получение всех кодов ---
def get_all_codes() -> list[str]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT code FROM users WHERE code IS NOT NULL")
    codes = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return codes

# --- Присвоение кодов пользователям без кода ---
def assign_codes():
    conn = get_conn()
    cur = conn.cursor()

    # Все существующие коды
    cur.execute("SELECT code FROM users WHERE code IS NOT NULL")
    existing_codes = {row[0] for row in cur.fetchall()}

    # Пользователи без кода
    cur.execute("SELECT user_id FROM users WHERE code IS NULL")
    code = 'AAAAA'
    for (user_id,) in cur.fetchall():
        while code in existing_codes:
            code = next_code(code)
        cur.execute("UPDATE users SET code=%s WHERE user_id=%s", (code, user_id))
        existing_codes.add(code)
        code = next_code(code)

    conn.commit()
    cur.close()
    conn.close()

# --- Получение всех данных пользователя ---
def get_user(user_id: str) -> dict:
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result or {}

# --- Создание или обновление пользователя ---
def upsert_user(user_id: str, **kwargs):
    conn = get_conn()
    cur = conn.cursor()

    columns = ", ".join(kwargs.keys())
    values = tuple(kwargs.values())
    placeholders = ", ".join(["%s"] * len(kwargs))

    update_clause = ", ".join(f"{k}=VALUES({k})" for k in kwargs.keys())

    sql = f"""
        INSERT INTO users (user_id, {columns})
        VALUES (%s, {placeholders})
        ON DUPLICATE KEY UPDATE {update_clause}
    """
    cur.execute(sql, (user_id, *values))
    conn.commit()
    cur.close()
    conn.close()

# --- Получение user_id по кодам ---
def get_user_ids_by_codes(codes: List[str]) -> List[str]:
    if not codes:
        return []
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        f"SELECT user_id FROM users WHERE code IN ({','.join(['%s']*len(codes))})",
        tuple(codes)
    )
    result = [str(row[0]) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return result
