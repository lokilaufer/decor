import os
from datetime import datetime
import requests
import json
from tqdm import tqdm


def logger(path):
    def __logger(old_function):
        def new_function(*args, **kwargs):
            result = old_function(*args, **kwargs)
            with open(path, 'a') as file:
                file.write(
                    f'{datetime.now()} - Function {old_function.__name__} was called with arguments: {args}, {kwargs}. Returned: {result}\n')
            return result

        return new_function

    return __logger


@logger('log.txt')
def get_photos(user_id, access_token):
    url = 'https://api.vk.com/method/photos.get'
    params = {
        'owner_id': user_id,
        'album_id': 'profile',
        'extended': 1,
        'count': 5,
        'v': '5.131',
        'access_token': access_token
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    photos = response.json()['response']['items']
    return photos


@logger('log.txt')
def download_photo(url, file_name):
    response = requests.get(url)
    response.raise_for_status()
    with open(file_name, 'wb') as file:
        file.write(response.content)


@logger('log.txt')
def save_photo_on_yandex_disk(file_path, yandex_token, yandex_folder):
    url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
    params = {
        'path': f'{yandex_folder}/{os.path.basename(file_path)}',
        'overwrite': 'true'
    }
    headers = {
        'Authorization': f'OAuth {yandex_token}'
    }
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    href = response.json()['href']
    with open(file_path, 'rb') as file:
        response = requests.put(href, files={'file': file})
        response.raise_for_status()


@logger('log.txt')
def save_photos_info_to_json(photos, json_file):
    photos_info = []
    for photo in photos:
        file_name = f"{photo['likes']['count']}.jpg"
        size = photo['sizes'][-1]['type']
        photos_info.append({
            "file_name": file_name,
            "size": size
        })
    with open(json_file, 'w') as file:
        json.dump(photos_info, file, ensure_ascii=False, indent=4)


def main():
    user_id = input('Введите id пользователя vk: ')
    yandex_token = input('Введите токен Яндекс.Диска: ')
    yandex_folder = input('Введите название папки на Яндекс.Диске: ')

    _create_folder(yandex_token, yandex_folder)

    photos = get_photos(user_id, VK_ACCESS_TOKEN)

    os.makedirs(yandex_folder, exist_ok=True)
    for photo in tqdm(photos, desc='Загрузка фотографий'):
        url = photo['sizes'][-1]['url']
        file_name = f"{photo['likes']['count']}.jpg"
        download_photo(url, file_name)
        save_photo_on_yandex_disk(file_name, yandex_token, yandex_folder)
        os.remove(file_name)

    save_photos_info_to_json(photos, 'photos_info.json')


@logger('log.txt')
def _create_folder(yandex_token, folder_name):
    headers = {
        "Authorization": f"OAuth {yandex_token}",
    }

    data = {
        "path": f"/{folder_name}"
    }

    response = requests.post("https://cloud-api.yandex.net/v1/disk/resources", headers=headers, json=data)

    if response.status_code == 201:
        print(f"Папка {response.json()['name']} успешно создана на Яндекс Диске.")
    else:
        print("Ошибка при создании папки на Яндекс Диске.")


if __name__ == '__main__':
    main()
