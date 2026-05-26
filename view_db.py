import asyncio
import asyncpg
from config import DATABASE_URL

ALLOWED_TABLES = frozenset({"birthdays", "admins", "user_birthdays", "user_settings"})

async def show_table(pool, table_name):
    if table_name not in ALLOWED_TABLES:
        print(f"⚠️ Ruxsat etilmagan jadval nomi: {table_name}")
        return
    async with pool.acquire() as conn:
        print(f"\n{'='*40}")
        print(f"Jadval: {table_name.upper()}")
        print(f"{'='*40}")
        
        # Get rows
        rows = await conn.fetch(f'SELECT * FROM {table_name}')
        
        if not rows:
            print("Jadval bo'sh.")
            return

        # Print column headers
        columns = rows[0].keys()
        header = " | ".join(f"{col:^15}" for col in columns)
        print(header)
        print("-" * len(header))
        
        # Print rows
        for row in rows:
            row_str = " | ".join(f"{str(row[col]):^15}" for col in columns)
            print(row_str)

async def main():
    print(f"Ulanilmoqda: {DATABASE_URL}")
    try:
        pool = await asyncpg.create_pool(DATABASE_URL)
        
        tables = ["birthdays", "admins", "user_birthdays", "user_settings"]
        for table in tables:
            await show_table(pool, table)
            
        await pool.close()
    except Exception as e:
        print(f"Xatolik yuz berdi: {e}")

if __name__ == '__main__':
    asyncio.run(main())
