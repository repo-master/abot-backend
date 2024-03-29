'''Warning! Never run this on an existing database!
This will (probably) wipe out the data!
Make sure to set the environment variable `DB_URI` to the database connection
'''

import asyncio


async def data_init():
    from abotcore.db import Base, Connection, get_engine

    engine = get_engine()
    conn: Connection

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def main():
    asyncio.run(data_init())


if __name__ == '__main__':
    main()
