import aiosqlite
import json
from config import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Create birthdays table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS birthdays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                day INTEGER NOT NULL,
                month INTEGER NOT NULL,
                year INTEGER,
                chat_id INTEGER,
                added_by INTEGER
            )
        ''')
        
        # Create admins table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                can_manage_admins BOOLEAN DEFAULT 0,
                permissions TEXT DEFAULT '{}'
            )
        ''')
        
        # Create user_birthdays table for personal use
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_birthdays (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                day INTEGER,
                month INTEGER,
                year INTEGER
            )
        ''')
        
        await db.commit()

async def add_birthday(name, day, month, year, chat_id, added_by):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT INTO birthdays (name, day, month, year, chat_id, added_by) VALUES (?, ?, ?, ?, ?, ?)',
            (name, day, month, year, chat_id, added_by)
        )
        await db.commit()

async def get_all_birthdays():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT name, day, month, year, chat_id FROM birthdays') as cursor:
            return await cursor.fetchall()

async def get_user_added_birthdays(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT name, day, month, year, chat_id FROM birthdays WHERE added_by = ?', (user_id,)) as cursor:
            return await cursor.fetchall()

async def delete_birthday(name, day, month, added_by):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'DELETE FROM birthdays WHERE name = ? AND day = ? AND month = ? AND added_by = ?',
            (name, day, month, added_by)
        )
        await db.commit()

async def add_admin(user_id, can_manage_admins=False, permissions=None):
    if permissions is None:
        permissions = {}
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT OR REPLACE INTO admins (user_id, can_manage_admins, permissions) VALUES (?, ?, ?)',
            (user_id, can_manage_admins, json.dumps(permissions))
        )
        await db.commit()

async def is_admin(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT 1 FROM admins WHERE user_id = ?', (user_id,)) as cursor:
            return await cursor.fetchone() is not None

async def get_admin_data(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT can_manage_admins, permissions FROM admins WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {"can_manage_admins": bool(row[0]), "permissions": json.loads(row[1])}
            return None

async def remove_admin(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
        await db.commit()

async def get_all_admins():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT user_id, can_manage_admins FROM admins') as cursor:
            return await cursor.fetchall()

async def set_user_birthday(user_id, name, day, month, year):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            'INSERT OR REPLACE INTO user_birthdays (user_id, name, day, month, year) VALUES (?, ?, ?, ?, ?)',
            (user_id, name, day, month, year)
        )
        await db.commit()

async def get_user_birthday(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT name, day, month, year FROM user_birthdays WHERE user_id = ?', (user_id,)) as cursor:
            return await cursor.fetchone()

async def get_all_user_birthdays():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT user_id, name, day, month, year FROM user_birthdays') as cursor:
            return await cursor.fetchall()
