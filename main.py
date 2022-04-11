import json, requests, hashlib
from pprint import pprint
from datetime import datetime
from progress.bar import Bar


class ProcessInd:
    bar = Bar('Выполнение', max=5)


class VkGetPhotos:
    URL = 'https://api.vk.com/method/'
    TOKEN = '958eb5d439726565e9333aa30e50e0f937ee432e927f0dbd541c541887d919a7c56f95c04217915c32008'

    def _get_user_id(self, screen_name):
        self.user_screen_name = screen_name
        URL_METHOD = 'users.get'
        params = {
            'user_ids': self.user_screen_name,
            'access_token': VkGetPhotos.TOKEN,
            'v': '5.131'
        }
        self.user_id = requests.get(VkGetPhotos.URL + URL_METHOD, params=params).json()['response'][0]['id']
        return self.user_id

    def _get_photos_info(self, data, photo_count):
        photo_info_dict_list = []
        names_list = []
        urls_list = []
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
        ProcessInd.bar.next()
        info_dict = {'info': photo_info_dict_list}
        with open('file_info.json', 'w', encoding='utf-8') as file:
            json.dump(info_dict, file)

        return urls_list

    def get_photos(self, user_screen_name):
        URL_METHOD = 'photos.get'
        self.album_id = input('Введите id скачиваемого альбома: ')
        self.photo_count = int(input('Введите кол-во скачиваемых фотографий: '))
        ProcessInd.bar.start()
        ProcessInd.bar.next()
        params = {
            'owner_id': self._get_user_id(user_screen_name),
            'album_id': self.album_id,
            'count': self.photo_count,
            'photo_sizes': '1',
            'extended': '1',
            'access_token': VkGetPhotos.TOKEN,
            'v': '5.131'
        }
        res = requests.get(VkGetPhotos.URL + URL_METHOD, params=params).json()
        ProcessInd.bar.next()
        if 'error' in res:
            with open('vk_errors.json', 'r', encoding='utf-8') as f:
                data = json.load(f)['errors'][str(res['error']['error_code'])]
                print('-------')
                print(data[0])
                print(data[1])
                if res['error']['error_code'] == 1 or res['error']['error_code'] == 10:
                    stop_word = 'exit'
                    ProcessInd.bar.finish()
                    return stop_word
            vk_user_screen_name_new = input()
            if vk_user_screen_name_new == 'p_end':
                stop_word = 'exit'
                ProcessInd.bar.finish()
                return stop_word
            ProcessInd.bar.finish()
            return self.get_photos(vk_user_screen_name_new)
        else:
            urls_list = self._get_photos_info(res, self.photo_count)
            ProcessInd.bar.next()

            return urls_list


class YaUploader:
    URL = 'https://cloud-api.yandex.net'

    def upload_photos(self, photos_urls_list, ya_token):
        if photos_urls_list == 'exit':
            return photos_urls_list
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'OAuth {ya_token}'
        }
        requests.put(YaUploader.URL + '/v1/disk/resources', headers=headers,
                     params={'path': 'VK_Photos_backup_Komarov'})
        with open('file_info.json', 'r', encoding='utf-8') as file:
            count = 0
            data = json.load(file)
            ProcessInd.bar.next()
            for url in photos_urls_list:
                requests.post(YaUploader.URL + '/v1/disk/resources/upload', headers=headers,
                              params={'path': f'VK_Photos_backup_Komarov/{data["info"][count]["file_name"]}',
                                      'url': url})
                count += 1
        print('-------')
        print('Фотографии загружены на Яндекс Диск')
        ProcessInd.bar.finish()
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
            n = 0
            while n in range(len(photos_dict['photos'])):
                photos_id_list.append(photos_dict['photos'][n]['fid'])
                n += 1
            self._get_photos_url_list(photos_id_list, user_id, photos_count)
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
            n = 0
            while n in range(len(photos_dict['photos'])):
                photos_id_list.append(photos_dict['photos'][n]['fid'])
                n += 1
            url_list = self._get_photos_info(photos_id_list, user_id, photos_count, album_id)

            return url_list

    def _get_photos_info(self, photos_id_list, user_id, photo_count, album_id=None):
        METHOD = 'photos.getInfo'
        if album_id == None:
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
        url_list = self._photo_name_urls(photos_info, photo_count)

        return url_list

    def _photo_name_urls(self, data, photo_count):
        photo_info_dict_list = []
        name_list = []
        url_list = []
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

            return url_list


if __name__ == '__main__':
    vk_photos_list = VkGetPhotos()
    ya_photos_uploader = YaUploader()
    ok_photos_list = OdnoklassnikiGetPhotos()
    social = input('Введите название соцсети (VK - Вконтакте, OK - Одноклассники, INST - Инстаграм): ').lower()
    cloud = input('Введите название облачного хранилища (YA - Яндекс Диск, GD - Google Drive): ').lower()
    user_command = social + cloud
    while user_command != 'exit':
        if user_command == 'vkya':
            vk_user_screen_name = input('Введите id пользователя: ')
            ya_user_token = input('Введите токен Яндекс Диска: ')
            user_command = ya_photos_uploader.upload_photos(vk_photos_list.get_photos(vk_user_screen_name),
                                                            ya_user_token)
        elif user_command == 'okya':
            ok_user_link = input('Введите ссылку на профиль пользователя: ')
            ya_user_token = input('Введите токен Яндекс Диска: ')
            user_command = ya_photos_uploader.upload_photos(ok_photos_list.get_photos(ok_user_link),
                                                            ya_user_token)
        elif user_command == 'another_action':
            social = input('Введите название соцсети (VK - Вконтакте, OK - Одноклассники, INST - Инстаграм): ').lower()
            cloud = input('Введите название облачного хранилища (YA - Яндекс Диск, GD - Google Drive): ').lower()
            user_command = social + cloud
    print('Работа программы завершена.')
    ok_photos_list.get_photos('https://ok.ru/valery.gogua')

