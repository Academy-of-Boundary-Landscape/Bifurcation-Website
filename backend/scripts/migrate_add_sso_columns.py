import asyncio

from sqlalchemy import inspect, text

from app.core.database import engine


async def _get_columns():
    async with engine.begin() as conn:
        return await conn.run_sync(
            lambda sync_conn: {column["name"] for column in inspect(sync_conn).get_columns("users")}
        )


async def _execute(statement: str) -> None:
    async with engine.begin() as conn:
        await conn.execute(text(statement))


async def main() -> None:
    columns = await _get_columns()

    column_statements = {
        "auth_provider": "ALTER TABLE users ADD COLUMN auth_provider VARCHAR(32)",
        "auth_subject": "ALTER TABLE users ADD COLUMN auth_subject VARCHAR(255)",
        "auth_user_id": "ALTER TABLE users ADD COLUMN auth_user_id VARCHAR(255)",
        "auth_last_sync_at": "ALTER TABLE users ADD COLUMN auth_last_sync_at TIMESTAMP",
    }

    for column_name, statement in column_statements.items():
        if column_name not in columns:
            await _execute(statement)
            print(f"added column: {column_name}")
        else:
            print(f"skip column: {column_name}")

    index_statements = [
        "CREATE INDEX IF NOT EXISTS ix_users_auth_provider ON users (auth_provider)",
        "CREATE INDEX IF NOT EXISTS ix_users_auth_subject ON users (auth_subject)",
        "CREATE INDEX IF NOT EXISTS ix_users_auth_user_id ON users (auth_user_id)",
        "CREATE INDEX IF NOT EXISTS ix_users_auth_last_sync_at ON users (auth_last_sync_at)",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_auth_provider_subject ON users (auth_provider, auth_subject)",
    ]

    for statement in index_statements:
        await _execute(statement)
        print(f"ensured: {statement}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
