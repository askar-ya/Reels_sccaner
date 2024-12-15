import asyncio
import asyncpg
import os
from datetime import datetime, timezone

from dotenv import load_dotenv

from Thoth.data_models import Reel

load_dotenv()

class DataBaseConnection:

    def __init__(self):
        self.conn = None

    async def connect(self):

        user = os.environ.get('PSQL_USER')
        database = os.environ.get('PSQL_NAME')
        password = os.environ.get('PSQL_PASS')

        self.conn = await asyncpg.connect(user=user,
                                          password=password,
                                          database=database)

    async def close(self):
        await self.conn.close()

    async def authors_by_tag(self, category: int):
        values = await self.conn.fetch(
            f"SELECT id FROM authors where category = {category} and last_update > now() - interval '14 day'"
        )

        return values

    async def author_by_id(self, author_id: int):
        values = await self.conn.fetch(
            f"SELECT name FROM authors where id = {author_id} "
        )

        if len(values) == 0:
            return False
        else:
            return values[0][0]

    async def author_update_stamp(self, author_id: int):
        now = datetime.now(timezone.utc)
        await self.conn.fetch(f"update authors set last_update = '{now}' where id = {author_id} ")

    async def save_reels(self, author_id: int, reel: Reel):
        values = f"({author_id}, '{reel.url}', {reel.likes}, {reel.comments}, {reel.views})"
        await self.conn.fetch(
            f"INSERT into reels (author, url, likes, comments, views) values {values}")

async def main():
    connection = DataBaseConnection()
    await connection.connect()
    reel = Reel('https://asda.com', 100, 10, 100000)
    await connection.save_reels(1, reel)
    await connection.close()


if __name__ == '__main__':
    asyncio.run(main())
