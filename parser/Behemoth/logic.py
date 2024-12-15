import json
import random

from Thoth.data_models import Reel

def get_proxy():
    """Получение прокси из файла"""
    proxy = True

    if proxy:
        # Получаем содержимое файла
        with open('storage/proxy.json', 'r', encoding='utf-8') as f:
            proxi = json.load(f)['ok']
        return proxi[0]
    else:
        return None


def get_work_account() -> dict:
    """Загружает куки"""
    with open('storage/cookies.json', 'r', encoding='utf-8') as f:
        cookies = json.load(f)['ok']

    return random.choice(cookies)


def load_header_patterns():
    """Загружает потерны"""
    with open('storage/patterns.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def insert_params_in_data(parameters: dict, patterns):
    """Вставляем аргументы в data запроса"""

    data = patterns['data_for_reels']
    for p in ['av', 'rev', '__hsi', 'fb_dtsg', 'jazoest', 'lsd', '__spin_r', '__spin_b', '__spin_t']:
        data[p] = parameters[p]

    data['variables'] = data['variables'].replace('userID', parameters['target_id'])

    return data


def insert_cur(data: dict, cur: str, user_id) -> dict:
    """обновляем курсор бд"""
    data['variables'] = (f'{{"after":"{cur}","before":null,"data":{{"include_feed_video":true,'
                         f'"page_size":12,"target_user_id":"{user_id}"}},"first":4,"last":null}}')
    return data


def data_headers(res_json, q_count):
    """Обработчик данных рилсов из ответа"""

    raw_data = res_json['data']['xdt_api__v1__clips__user__connection_v2']['edges']
    valid_reels = []

    for n, video in enumerate(raw_data):
        video = video['node']['media']
        if video['play_count'] is not None:
            play_count = video['play_count']
        elif video['view_count'] is not None:
            play_count = video['view_count']
        else:
            play_count = 1

        if play_count >= q_count:

            likes = video['like_count'] if 'like_count' in video else 0

            comments = video['comment_count'] if 'comment_count' in video else 0

            reel = Reel(f'https://www.instagram.com/reel/{video['code']}',
                        likes, play_count, comments)
            valid_reels.append(reel)

    return valid_reels


def check_end(res_json):
    """Проверяет последний ли это срез"""
    res = res_json['data']['xdt_api__v1__clips__user__connection_v2']['page_info']['has_next_page']
    if res:
        return False
    else:
        return True

def save_reels(reels: list, file: str):
    out = ''
    for reel in reels:
        out += f'{reel["url"], reel['play_count'], reel['like_count'], reel['comment_count']}\n'
    with open(file, 'a', encoding='utf-8') as f:
        f.write(out)