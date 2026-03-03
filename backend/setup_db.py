"""
KIP Database Setup Script
Run this to create all tables without Alembic.
For development and initial deployment.

Usage: python setup_db.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def main():
    print("🗄  KIP Database Setup")
    print("=" * 40)

    try:
        from models.database import engine, Base, init_db
        print("✓ Models imported")
        await init_db()
        print("✓ All tables created successfully")
        print()
        print("Tables created:")
        async with engine.connect() as conn:
            result = await conn.execute(
                __import__('sqlalchemy').text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' ORDER BY table_name"
                )
            )
            for row in result:
                print(f"  - {row[0]}")
    except Exception as e:
        print(f"✗ Error: {e}")
        print()
        print("Make sure:")
        print("  1. PostgreSQL is running")
        print("  2. DATABASE_URL in .env points to your database")
        print("  3. pip install -r requirements.txt has been run")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
