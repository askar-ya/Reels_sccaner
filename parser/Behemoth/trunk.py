import aiohttp


from Behemoth.logic import get_proxy, get_work_account
from Behemoth.logic import load_header_patterns
from Behemoth.logic import insert_params_in_data, insert_cur
from Behemoth.logic import data_headers, check_end
from Behemoth.loger import log

from Thoth.psql import DataBaseConnection


import json
import re
import atexit

from aiohttp_socks import ProxyConnector

TIME_OUT = 30
MAX_REDIRECT = 50


class ParsAccountReels:
    def __init__(self, author_id: int, q_count: int, steam_count: int):

        self.author_id = author_id
        self.q_count = q_count
        self.profile_cookies = get_work_account()
        self.proxy = get_proxy()
        self.proxy_connector = ProxyConnector.from_url(self.proxy)

        self.max_retries = 25
        self.time_out = 30

        self.session = None

        self.patterns = load_header_patterns()
        self.cur = None
        self.reels = []
        self.order = 0
        self.steam = steam_count
        self.lof_file = f"logs/steam_{steam_count}.log"

    async def loger(self, *args):
        await log(self.lof_file, *args)


    def swap_work_profile(self, status: str):
        """Меняет рабочий аккаунт"""

        with open("storage/cookies.json", 'r', encoding='utf-8', ) as f:
            """Открываем файл с аккаунтами"""

            accounts = json.load(f) # Загружаем список рабочих аккаунтов

        # Проверяем статус аккаунта
        if self.profile_cookies in accounts['ok']:
            with open('storage/cookies.json', 'w', encoding='utf-8') as f:
                accounts['ok'].remove(self.profile_cookies) # добавляем в неактивные
                accounts[status].append(self.profile_cookies)
                json.dump(accounts, f, indent=4) # обновляем файл

        self.profile_cookies = get_work_account() # Обновляем рабочий аккаунт


    def change_proxy(self):
        """Меняет рабочий прокси"""

        with open("storage/proxy.json", 'r', encoding='utf-8', ) as f:
            """Открываем файл с прокси"""
            proxies = json.load(f) # Загружаем список прокси

        # Проверяем не добавлен ли он уже в неактивные
        if self.proxy in proxies['ok']:
            with open("storage/proxy.json", 'w', encoding='utf-8') as f:
                proxies['ok'].remove(self.proxy) # добавляем в неактивные
                proxies['end'].append(self.proxy)  # добавляем в неактивные
                json.dump(proxies, f, indent=4) # обновляем файл
        self.proxy = get_proxy() # Обновляем рабочий прокси

    async def refresh_session(self):
        await self.session.close()
        connector = ProxyConnector.from_url(self.proxy)
        self.session = aiohttp.ClientSession(connector=connector,
                                             timeout=aiohttp.ClientTimeout(total=self.time_out))

    def insert_params_in_headers(self, parameters: dict, referer) -> dict:
        """Вставляем аргументы в headers запроса"""
        patterns = self.patterns
        cookies = self.profile_cookies
        headers_for_reels = patterns['headers_for_reels']
        headers_for_reels['referer'] = referer
        headers_for_reels['x-bloks-version-id'] = parameters['x_bloks_version_id']
        headers_for_reels['x-csrftoken'] = cookies['csrftoken']
        headers_for_reels['x-fb-lsd'] = parameters['lsd']
        headers_for_reels['x-ig-app-id'] = parameters['app_id']
        return headers_for_reels


    async def request_handler(self, url, method: str='get',
                              headers: dict=None, data: dict=None, out_f: str= 'json'):

        try:
            args = {
                "url": url, "headers": headers, "data": data,
                "cookies": self.profile_cookies, "timeout": self.time_out
            }
            if method == 'get':
                request = await self.session.get(**args)
            else:
                request = await self.session.post(**args)
            if request.status == 200:
                if out_f[:4] == 'json':
                    try:
                        data =  await request.json()
                    except json.decoder.JSONDecodeError:
                        if out_f == 'json':
                            return await self.request_handler(url, method=method, headers=headers,
                                                  data=data, out_f=out_f)
                        elif out_f == 'json_n':
                            data = ''
                    return {'ok': True, 'data': data}
                elif out_f == 'text':
                    data = await request.text()
                return {'ok': True, 'data': data}

            elif request.status in [560, 572]:
                await self.loger('account time ban')
                self.swap_work_profile('time_ban')

        except aiohttp.ConnectionTimeoutError:
            await self.loger('timout')
            self.change_proxy()

        except aiohttp.ClientConnectionError:
            await self.loger('account time ban')


        except Exception as e:
            print(e)
            print(123)
            await self.loger(str(e))

        return await self.request_handler(url, method=method, headers=headers, data=data, out_f=out_f)


    async def get_base_html(self, account_name):
        """Получаем базовый html аккаунта, для дальнейших запросов"""

        # получаем все заголовки для запроса
        headers = self.patterns['headers_for_html']
        headers['referer'] = headers['referer'].replace('name', account_name)

        url = f'https://www.instagram.com/{account_name}/reels/'

        response = await self.request_handler(url, headers=headers, out_f='text')

        if response['ok']:
            base = response['data']
        else:
            return {'ok': False, 'error': 'fuck!'}

        # проверяем статус ответа
        return base


    async def param_from_html(self, html, account_name) -> dict:
        """Получаем аргументы из html"""
        args = {
            'x_bloks_version_id': r'."versioningID":"(.*?)"',
            'lsd': r'"LSD",.*?,."token":"(.*?)"',
            'app_id': r',"APP_ID":"(.*?)"',
            'av': r'actorID":"(.*?)"',
            'rev': r'"rev":(.*?).,',
            '__hsi': r',"hsi":"(.*?)"',
            'fb_dtsg': r'."DTSGInitialData",..,."token":"(.*?)"',
            'jazoest': r'&jazoest=(.*?)"',
            '__spin_r': r'"__spin_r":(.*?),',
            '__spin_b': r',"__spin_b":"(.*?)",',
            '__spin_t': r',"__spin_t":(.*?),',
            'target_id': r'"target_id":"(.*?)"'
        }

        try:
            for parm in args:
                new = re.search(args[parm], html, flags=re.DOTALL | re.MULTILINE).group(1)
                args[parm] = new

            return args
        except Exception as e:
            self.change_proxy()
            await self.refresh_session()
            await self.loger(str(e))
            html = await self.get_base_html(account_name)
            return await self.param_from_html(html, account_name)


    async def first_videos(self, parameters) -> dict:
        headers = self.insert_params_in_headers(parameters,
                                           self.patterns['headers_for_html']['referer'])
        data = insert_params_in_data(parameters, self.patterns)

        response = await self.request_handler('https://www.instagram.com/graphql/query', method='post',
                                              headers=headers, data=data, out_f='json')
        # Делаем запрос к api для получения первых 12ти видео
        if response['ok']:
            first = response['data']
        else:
            return {'ok': False, 'error': 'fuck!'}

        # Проверяем статус запроса
        await self.loger(f'Получено: {12} видео')
        return {'ok': True, 'res': first}


    async def subsequent_videos(self, parameters, cur) -> dict:
        data = insert_params_in_data(parameters, self.patterns)
        data = insert_cur(data, cur, parameters['target_id'])
        headers = self.insert_params_in_headers(parameters,
                                           self.patterns['headers_for_html']['referer'])

        # Делаем запрос для получения следующих 12ти видео
        response = await self.request_handler('https://www.instagram.com/graphql/query', method='post',
                                               headers=headers, data=data, out_f='json_n')

        if response['ok']:
            response = response['data']
        else:
            return {'ok': False, 'error': 'fuck!'}

        if response == '':
            await self.loger(f'всего получено: {self.order * 12} видео,'
                             f'валидных: {len(self.reels)}')

            return {'ok': True, 'next': False, 'data': self.reels}
        else:
            self.order += 1
            await self.loger(f'Получено: {self.order * 12} видео')

            if 'errors' in response:
                await self.loger(f'всего получено: {self.order * 12} видео,'
                                 f'валидных: {len(self.reels)}')

                return {'ok': True, 'next': False, 'data': self.reels}

            elif 'data' in  response:
                videos = data_headers(response, self.q_count)
                self.reels.extend(videos)
                if check_end(response):
                    await self.loger(f'всего получено: {self.order * 12} видео,'
                                     f'валидных: {len(self.reels)}')

                    return {'ok': True, 'next': False, 'data': self.reels}

            return {'ok': True, 'res': response, 'next': True}


    async def save_reels(self, conn: DataBaseConnection):
        for reel in self.reels:
            await conn.save_reels(self.author_id, reel)
        await conn.author_update_stamp(self.author_id)
        await conn.close()


    async def pars(self) -> dict:



        psql_con = DataBaseConnection()


        await psql_con.connect()
        author_name = await psql_con.author_by_id(self.author_id)

        connector = ProxyConnector.from_url(self.proxy)
        self.session = aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=self.time_out))

        base_html = await self.get_base_html(author_name)

        # Пробуем получить доп параметры для запроса рилсов
        parameters = await self.param_from_html(base_html, author_name)

        first_request_json = await self.first_videos(parameters)

        if first_request_json['ok']:
            videos = data_headers(first_request_json['res'], self.q_count)
            self.reels.extend(videos)
        else:
            return {'ok': False, 'error': first_request_json['error']}

        # Проверяем конец-ли это
        self.order = 1
        if check_end(first_request_json['res']):

            await self.loger(f'всего получено: {self.order * 12} видео,'
                             f'валидных: {len(self.reels)}')

            await self.save_reels(psql_con)
            return {'ok': True}

        self.cur = first_request_json['res']['data'][
            'xdt_api__v1__clips__user__connection_v2']['page_info']['end_cursor']

        while True:
            # Получаем курсор для следующего запроса
            subsequent_requests = await self.subsequent_videos(parameters, self.cur)
            if subsequent_requests['ok'] and subsequent_requests['next']:
                self.cur = subsequent_requests['res']['data'][
                    'xdt_api__v1__clips__user__connection_v2']['page_info']['end_cursor']
            else:
                await self.save_reels(psql_con)
                await self.session.close()
                await psql_con.close()
                return {'ok': True}

    def at_exit(self):
        self.session.close()