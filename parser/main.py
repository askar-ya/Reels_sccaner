from Behemoth import trunk
from Thoth.psql import DataBaseConnection
import asyncio


async def check(reels):
    if reels['ok']:
        return True
    else:
        if 'error' in reels:
            if reels['error'] == 'account':
                print('Аккаунт закрытый или удален !')
            else:
                print(f'Непредвиденная ошибка, код: {reels['error']}')
                return 'exit'


async def pars(author_id: int, steam: int):
    q_view = 100000

    parser = trunk.ParsAccountReels(author_id, q_view, steam)
    valid = await check(await parser.pars())
    if valid == 'exit':
        return 'exit'


async def main(steams: int):
    conn = DataBaseConnection()
    await conn.connect()

    authors = await conn.authors_by_tag(1)
    authors_len = len(authors)

    for author in range(0, authors_len, steams):
        tasks = []
        for steam in range(1, steams+1):
            tasks.append(
                pars(authors[author+steam-1][0], steam)
            )

        print(author)

        await asyncio.gather(*tasks)


steams_count = 1

try:
    asyncio.run(main(steams_count))
except KeyboardInterrupt:
    clear = input("\nОчистить логи? (yes/no): ")
    if clear in ['yes', 'y', 'Yes', 'Y']:
        for i in range(1, steams_count+1):
            with open(f'logs/steam_{i}.log', 'w') as file:
                file.write('')


print('Все!')
