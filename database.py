import asyncpg
import json
import logging
from config import DATABASE_URL

# Global connection pool
_pool: asyncpg.Pool | None = None

async def get_pool() -> asyncpg.Pool:
    """Return the global connection pool, creating it if needed."""
    global _pool
    if _pool is None:
        raise RuntimeError("Database pool is not initialized. Call init_db() first.")
    return _pool

async def init_db():
    """Initialize the PostgreSQL connection pool and create tables."""
    global _pool
    try:
        _pool = await asyncpg.create_pool(
            dsn=DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=60,
        )
        logging.info("✅ PostgreSQL ulanish muvaffaqiyatli yaratildi.")
    except Exception as e:
        logging.critical(f"❌ PostgreSQL ga ulanib bo'lmadi: {e}")
        raise

    async with _pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS birthdays (
                id        SERIAL PRIMARY KEY,
                name      TEXT    NOT NULL,
                day       INTEGER NOT NULL,
                month     INTEGER NOT NULL,
                year      INTEGER,
                chat_id   BIGINT,
                added_by  BIGINT
            )
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                user_id          BIGINT  PRIMARY KEY,
                can_manage_admins BOOLEAN DEFAULT FALSE,
                permissions      TEXT    DEFAULT '{}'
            )
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_birthdays (
                user_id BIGINT PRIMARY KEY,
                name    TEXT,
                day     INTEGER,
                month   INTEGER,
                year    INTEGER
            )
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id    BIGINT PRIMARY KEY,
                remind_days TEXT   DEFAULT '[0,1,2]'
            )
        ''')

    logging.info("✅ Jadvallar tayyor.")


async def close_db():
    """Close the connection pool gracefully."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logging.info("🔌 PostgreSQL ulanishi yopildi.")


# ──────────────────────────────────────────
# Birthdays
# ──────────────────────────────────────────

async def add_birthday(name, day, month, year, chat_id, added_by):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            'INSERT INTO birthdays (name, day, month, year, chat_id, added_by) VALUES ($1, $2, $3, $4, $5, $6)',
            name, day, month, year, chat_id, added_by
        )

async def get_all_birthdays():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch('SELECT name, day, month, year, chat_id, added_by FROM birthdays')
        return [tuple(r) for r in rows]

async def get_user_added_birthdays(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            'SELECT name, day, month, year, chat_id FROM birthdays WHERE added_by = $1',
            user_id
        )
        return [tuple(r) for r in rows]

async def delete_birthday(name, day, month, added_by):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM birthdays WHERE name = $1 AND day = $2 AND month = $3 AND added_by = $4',
            name, day, month, added_by
        )


# ──────────────────────────────────────────
# Admins
# ──────────────────────────────────────────

async def add_admin(user_id, can_manage_admins=False, permissions=None):
    if permissions is None:
        permissions = {}
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            '''
            INSERT INTO admins (user_id, can_manage_admins, permissions)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE
                SET can_manage_admins = EXCLUDED.can_manage_admins,
                    permissions       = EXCLUDED.permissions
            ''',
            user_id, can_manage_admins, json.dumps(permissions)
        )

async def is_admin(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchval('SELECT 1 FROM admins WHERE user_id = $1', user_id)
        return row is not None

async def get_admin_data(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT can_manage_admins, permissions FROM admins WHERE user_id = $1',
            user_id
        )
        if row:
            return {
                "can_manage_admins": bool(row["can_manage_admins"]),
                "permissions": json.loads(row["permissions"]),
            }
        return None

async def remove_admin(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute('DELETE FROM admins WHERE user_id = $1', user_id)

async def get_all_admins():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch('SELECT user_id, can_manage_admins FROM admins')
        return [tuple(r) for r in rows]


# ──────────────────────────────────────────
# User Birthdays (personal)
# ──────────────────────────────────────────

async def set_user_birthday(user_id, name, day, month, year):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            '''
            INSERT INTO user_birthdays (user_id, name, day, month, year)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (user_id) DO UPDATE
                SET name  = EXCLUDED.name,
                    day   = EXCLUDED.day,
                    month = EXCLUDED.month,
                    year  = EXCLUDED.year
            ''',
            user_id, name, day, month, year
        )

async def get_user_birthday(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT name, day, month, year FROM user_birthdays WHERE user_id = $1',
            user_id
        )
        return tuple(row) if row else None

async def get_all_user_birthdays():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch('SELECT user_id, name, day, month, year FROM user_birthdays')
        return [tuple(r) for r in rows]


# ──────────────────────────────────────────
# User Reminder Settings
# ──────────────────────────────────────────

async def get_user_remind_settings(user_id):
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT remind_days FROM user_settings WHERE user_id = $1',
            user_id
        )
        return json.loads(row["remind_days"]) if row else [0, 1, 2]

async def set_user_remind_settings(user_id, days):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            '''
            INSERT INTO user_settings (user_id, remind_days)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE
                SET remind_days = EXCLUDED.remind_days
            ''',
            user_id, json.dumps(sorted(days))
        )
