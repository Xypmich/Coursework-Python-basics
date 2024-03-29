import hashlib
import json
import requests
import time
from datetime import datetime

from progress.bar import Bar


class VkGetPhotos:
    URL = 'https://api.vk.com/method/'
    TOKEN = 'a67f00c673c3d4b12800dd0ba29579ec56d804f3c5f3bbcef5328d4b3981fa5987b951cf2c8d8b24b9abd'

    def _get_user_id(self, screen_name):
        self.user_screen_name = screen_name
        URL_METHOD = 'users.get'
        params = {
            'user_ids': self.user_screen_name,
            'access_token': VkGetPhotos.TOKEN,
            'v': '5.131'
        }
        self.user_id = requests.get(VkGetPhotos.URL + URL_METHOD, params=params).json()
        if 'error' in self.user_id:
            with open('vk_errors.json', 'r', encoding='utf-8') as f:
                data = json.load(f)['errors'][str(self.user_id['error']['error_code'])]
                print('-------')
                print(data[0])
                print(data[1])
                if self.user_id['error']['error_code'] == 1 or self.user_id['error']['error_code'] == 10:
                    stop_word = 'exit'
                    return stop_word
            vk_user_screen_name_new = input()
            if vk_user_screen_name_new == 'p_end':
                stop_word = 'exit'
                return stop_word
            return self.get_photos(vk_user_screen_name_new)
        else:
            return self.user_id['response'][0]['id']

    def _get_photos_info(self, data, photo_count):
        photo_info_dict_list = []
        names_list = []
        urls_list = []
        print('-------')
        print(f'Получаю список изображений с vk.com...\n')
        bar = Bar('Выполнение', max=photo_count)
        bar.start()
        for i in range(photo_count):
            likes = str(data['response']['items'][i]['likes']['count'])
            upload_date = datetime.utcfromtimestamp(data['response']['items'][i]['date']).strftime('%d.%m.%Y')
            sizes_list = data['response']['items'][i]['sizes']
            photo_name = f'{likes}.jpg'
            photo_name_2 = f'{likes}_{upload_date}.jpg'
            width_backup = 0
            img_url = None
            size_type = None
            for img in sizes_list:
                if img['width'] > width_backup:
                    width_backup = img['width']
                    img_url = img['url']
                    size_type = img['type']
                else:
                    continue
            if photo_name in names_list:
                photo_info_dict = {
                    'file_name': photo_name_2,
                    'size': size_type
                }
            else:
                photo_info_dict = {
                    'file_name': photo_name,
                    'size': size_type
                }
            photo_info_dict_list.append(photo_info_dict)
            names_list.append(photo_name)
            urls_list.append(img_url)
            if i + 1 >= data['response']['count']:
                break
            bar.next()
            time.sleep(0.5)
        bar.finish()
        print(f'\nСписок изображений получен.')
        info_dict = {'info': photo_info_dict_list}
        with open('file_info.json', 'w', encoding='utf-8') as file:
            json.dump(info_dict, file)

        return urls_list

    def get_photos(self, user_screen_name):
        URL_METHOD = 'photos.get'
        album_id = input('Введите id скачиваемого альбома: ')
        photo_count = int(input('Введите кол-во скачиваемых фотографий: '))
        params = {
            'owner_id': self._get_user_id(user_screen_name),
            'album_id': album_id,
            'count': photo_count,
            'photo_sizes': '1',
            'extended': '1',
            'access_token': VkGetPhotos.TOKEN,
            'v': '5.131'
        }
        res = requests.get(VkGetPhotos.URL + URL_METHOD, params=params).json()
        if 'error' in res:
            with open('vk_errors.json', 'r', encoding='utf-8') as f:
                data = json.load(f)['errors'][str(res['error']['error_code'])]
                print('-------')
                print(data[0])
                print(data[1])
                if res['error']['error_code'] == 1 or res['error']['error_code'] == 10:
                    stop_word = 'exit'
                    return stop_word
            vk_user_screen_name_new = input()
            if vk_user_screen_name_new == 'p_end':
                stop_word = 'exit'
                return stop_word
            return self.get_photos(vk_user_screen_name_new)
        else:
            urls_list = self._get_photos_info(res, photo_count)

            return urls_list


class YaUploader:
    URL = 'https://cloud-api.yandex.net'

    def upload_photos(self, photos_urls_list, ya_token, social):
        if photos_urls_list == 'exit':
            return photos_urls_list
        if social == 'vk':
            DIR = 'VK_Photos_backup_Komarov'
        elif social == 'ok':
            DIR = 'OK_Photos_backup_Komarov'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'OAuth {ya_token}'
        }
        dir_resp = requests.put(YaUploader.URL + '/v1/disk/resources', headers=headers,
                     params={'path': DIR})
        if dir_resp.json()['error']:
            print('-------')
            print('Ошибка при создании папки на Яндекс Диске!')
            print(f'Ошибка: {dir_resp.json()["error"]}\nОписание ошибки: {dir_resp.json()["description"]}')
            print('Работа программы завершена.')
            stop_word = 'exit'
            return stop_word
        print('-------')
        print(f'Загружаю изображения на Яндекс Диск...\n')
        bar = Bar('Выполнение', max=len(photos_urls_list))
        bar.start()
        with open('file_info.json', 'r', encoding='utf-8') as file:
            count = 0
            data = json.load(file)
            for url in photos_urls_list:
                photo_upload_resp = requests.post(YaUploader.URL + '/v1/disk/resources/upload', headers=headers,
                              params={'path': f'{DIR}/{data["info"][count]["file_name"]}',
                                      'url': url})
                if photo_upload_resp.json()['error']:
                    print('-------')
                    print('Ошибка при загрузке изображения на Яндекс Диск!')
                    print(f'Ошибка: {dir_resp.json()["error"]}\nОписание ошибки: {dir_resp.json()["description"]}')
                    print('Работа программы завершена.')
                    stop_word = 'exit'
                    return stop_word
                count += 1
                bar.next()
                time.sleep(0.5)
        bar.finish()
        print(f'\nФотографии загружены на Яндекс Диск')
        next_command = input('Загрузить другие фото? (yes/no): ').lower()
        while next_command != 'yes' and next_command != 'no':
            print('-------', 'Неизвестная команда!', sep='\n')
            next_command = input('Загрузить другие фото? (yes/no): ').lower()
        if next_command == 'y':
            final_command = 'another_action'
        else:
            final_command = 'exit'

        return final_command


class OdnoklassnikiGetPhotos:
    URL = 'https://api.ok.ru/fb.do'
    SESSION_KEY = 'tkn1MCwOquqkbB21ygA5d2cO88dzwgTYcay76ED02qpGFRZmPmdA358ohjMeeoCsHMvDa'
    SESSION_SECRET_KEY = 'f56eb5c8470dfecab17a32c08827de10'
    APP_ID = '512001283091'
    APP_KEY = 'CEBFJIKGDIHBABABA'

    def _get_user_id(self, account_link):
        METHOD = 'url.getInfo'
        params = {
            'format': 'json',
            'method': METHOD,
            'url': account_link,
            'application_key': OdnoklassnikiGetPhotos.APP_KEY,
            'session_key': OdnoklassnikiGetPhotos.SESSION_KEY
        }
        sig = self._get_md5_sig(params)
        user_id = requests.get(OdnoklassnikiGetPhotos.URL, params=sig).json()
        if user_id['error_code']:
            print('-------')
            print('Ошибка при получении id пользователя!')
            return self.error_finder(user_id)

        return user_id['objectId']

    def _get_user_albums(self, user_id):
        METHOD = 'photos.getAlbums'
        params = {
            'format': 'json',
            'fid': user_id,
            'method': METHOD,
            'application_key': OdnoklassnikiGetPhotos.APP_KEY,
            'session_key': OdnoklassnikiGetPhotos.SESSION_KEY
        }
        sig = self._get_md5_sig(params)
        photo_albums = requests.get(OdnoklassnikiGetPhotos.URL, params=sig).json()
        if photo_albums['error_code']:
            print('-------')
            print('Ошибка при получении списка альбомов пользователя!')
            return self.error_finder(photo_albums)
        photo_albums_dict = {album['title']: album['aid'] for album in photo_albums['albums']}

        return photo_albums_dict

    def _get_md5_sig(self, params_dict):
        params_dict_copy = params_dict.copy()
        [params_dict_copy.pop(key, '') for key in ['access_token']]
        lexico_params = sorted(params_dict_copy.items())
        md5_basic = ''
        for val in lexico_params:
            md5_basic = f'{md5_basic}{val[0]}={val[1]}'
        sig = hashlib.md5(f'{md5_basic}{OdnoklassnikiGetPhotos.SESSION_SECRET_KEY}'.encode()).hexdigest()
        params_dict['sig'] = sig

        return params_dict

    def get_photos(self, user_account_link):
        photos_id_list = []
        user_id = str(self._get_user_id(user_account_link))
        albums_list_dict = self._get_user_albums(user_id)
        print('-------')
        print('Доступные альбомы пользователя:')
        print(*[album_title for album_title in albums_list_dict.keys()], sep='\n')
        print('Personal - для скачивания личных фото')
        print('-------')
        selected_album = input('Выберите нужный альбом: ')
        while selected_album not in albums_list_dict and selected_album != 'Personal':
            print('Введено неверное имя альбома!')
            selected_album = input('Выберите нужный альбом: ')
        photos_count = input('Введите кол-во загружаемых фотографий: ')
        if selected_album == 'Personal':
            METHOD = 'photos.getUserPhotos'
            params = {
                'method': METHOD,
                'format': 'json',
                'fid': user_id,
                'count': photos_count,
                'application_key': OdnoklassnikiGetPhotos.APP_KEY,
                'session_key': OdnoklassnikiGetPhotos.SESSION_KEY
            }
            sig = self._get_md5_sig(params)
            photos_dict = requests.get(OdnoklassnikiGetPhotos.URL, params=sig).json()
            if photos_dict['error_code']:
                print('-------')
                print('Ошибка при получении списка изображений альбома пользователя!')
                return self.error_finder(photos_dict)
            n = 0
            while n in range(len(photos_dict['photos'])):
                photos_id_list.append(photos_dict['photos'][n]['fid'])
                n += 1
            url_list = self._get_photos_info(photos_id_list, user_id, photos_count)
        else:
            album_id = albums_list_dict[selected_album]
            METHOD = 'photos.getUserAlbumPhotos'
            params = {
                'method': METHOD,
                'format': 'json',
                'aid': album_id,
                'count': photos_count,
                'application_key': OdnoklassnikiGetPhotos.APP_KEY,
                'session_key': OdnoklassnikiGetPhotos.SESSION_KEY
            }
            sig = self._get_md5_sig(params)
            photos_dict = requests.get(OdnoklassnikiGetPhotos.URL, params=sig).json()
            if photos_dict['error_code']:
                print('-------')
                print('Ошибка при получении списка изображений альбома пользователя!')
                return self.error_finder(photos_dict)
            n = 0
            while n in range(len(photos_dict['photos'])):
                photos_id_list.append(photos_dict['photos'][n]['fid'])
                n += 1
            url_list = self._get_photos_info(photos_id_list, user_id, photos_count, album_id)

        return url_list

    def _get_photos_info(self, photos_id_list, user_id, photo_count, album_id=None):
        METHOD = 'photos.getInfo'
        if album_id is None:
            params = {
                'method': METHOD,
                'format': 'json',
                'fid': user_id,
                'fields': 'photo.PIC640X480, photo.LIKE_COUNT, photo.CREATED_MS',
                'photo_ids': ','.join(photos_id_list),
                'application_key': OdnoklassnikiGetPhotos.APP_KEY,
                'session_key': OdnoklassnikiGetPhotos.SESSION_KEY
            }
        else:
            params = {
                'method': METHOD,
                'format': 'json',
                'fid': user_id,
                'aid': album_id,
                'fields': 'photo.PIC640X480, photo.LIKE_COUNT, photo.CREATED_MS',
                'photo_ids': ','.join(photos_id_list),
                'application_key': OdnoklassnikiGetPhotos.APP_KEY,
                'session_key': OdnoklassnikiGetPhotos.SESSION_KEY
            }
        sig = self._get_md5_sig(params)
        photos_info = requests.get(OdnoklassnikiGetPhotos.URL, params=sig).json()
        if photos_info['error_code']:
            print('-------')
            print('Ошибка при получении информации о фото пользователя!')
            return self.error_finder(photos_info)
        url_list = self._photo_name_urls(photos_info, photo_count)

        return url_list

    def _photo_name_urls(self, data, photo_count):
        photo_info_dict_list = []
        name_list = []
        url_list = []
        print('-------')
        print(f'Получаю список изображений с ok.ru...\n')
        bar = Bar('Выполнение', max=len(photo_count))
        bar.start()
        for i in range(int(photo_count)):
            likes = data['photos'][i]['like_count']
            photo_url = data['photos'][i]['pic640x480']
            upload_date = datetime.utcfromtimestamp(data['photos'][i]['created_ms'] / 1000).strftime('%d.%m.%Y')
            photo_name = f'{likes}.jpg'
            photo_name_2 = f'{likes}_{upload_date}.jpg'
            if photo_name in name_list:
                photo_info_dict = {
                    'file_name': photo_name_2,
                    'size': '640x480'
                }
            else:
                photo_info_dict = {
                    'file_name': photo_name,
                    'size': '640x480'
                }
            photo_info_dict_list.append(photo_info_dict)
            name_list.append(photo_name)
            url_list.append(photo_url)
            if i + 1 > int(photo_count):
                break
            info_dict = {'info': photo_info_dict_list}
            with open('file_info.json', 'w', encoding='utf-8') as file:
                json.dump(info_dict, file)
            bar.next()
            time.sleep(0.5)
        bar.finish()
        print(f'\nСписок изображений получен.')

        return url_list

    def error_finder(self, response):
        if response['error_code'] == 100:
            with open('ok_errors.json', 'r', encoding='utf-8') as file:
                with open('ok_errors_100_ext.json', 'r', encoding='utf-8') as f:
                    error_ = json.load(file)
                    error_ext = json.load(f)
                    print(f'Ошибка: {error_[response["error_code"]]}\n'
                          f'Описание ошибки: {error_ext[response["error_data"]]}')
        else:
            with open('ok_errors.json', 'r', encoding='utf-8') as file:
                error_ = json.load(file)
                print(f'Ошибка: {error_[response["error_code"]]}')
        print('Работа программы завершена.')
        stop_word = 'exit'

        return stop_word


def run_uploader(user_command, social, ya_user_token):
    while user_command != 'exit':
        if user_command == 'vk':
            vk_user_screen_name = input('Введите id пользователя: ')
            user_command = ya_photos_uploader.upload_photos(vk_photos_list.get_photos(vk_user_screen_name),
                                                            ya_user_token, social)
        elif user_command == 'ok':
            ok_user_link = input('Введите ссылку на профиль пользователя: ')
            user_command = ya_photos_uploader.upload_photos(ok_photos_list.get_photos(ok_user_link),
                                                            ya_user_token, social)
        elif user_command == 'another_action':
            social = input('Введите название соцсети (VK - Вконтакте, OK - Одноклассники): ').lower()
            user_command = social
    print('Работа программы завершена.')


if __name__ == '__main__':
    vk_photos_list = VkGetPhotos()
    ya_photos_uploader = YaUploader()
    ok_photos_list = OdnoklassnikiGetPhotos()
    social = input('Введите название соцсети (VK - Вконтакте, OK - Одноклассники): ').lower()
    ya_user_token = input('Введите токен Яндекс Диска: ')
    user_command = social

    run_uploader(user_command, social, ya_user_token)
