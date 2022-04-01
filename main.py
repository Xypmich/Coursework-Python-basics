import json
import requests
from pprint import pprint
from datetime import datetime


class VkGetPhotos:
    URL = 'https://api.vk.com/method/'
    TOKEN = '958eb5d439726565e9333aa30e50e0f937ee432e927f0dbd541c541887d919a7c56f95c04217915c32008'

    def __init__(self, vk_user_screen_name: str):
        self.user_screen_name = vk_user_screen_name

    def _get_user_id(self):
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
            photo_name = likes + '.jpg'
            photo_name_2 = likes + '_' + upload_date + '.jpg'
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
        info_dict = {'info': photo_info_dict_list}
        with open('file_info.json', 'w', encoding='utf-8') as file:
            json.dump(info_dict, file)
        return urls_list

    def get_photos(self):
        URL_METHOD = 'photos.get'
        self.album_id = input('Введите id скачиваемого альбома: ')
        self.photo_count = int(input('Введите кол-во скачиваемых фотографий: '))
        params = {
            'owner_id': self._get_user_id(),
            'album_id': self.album_id,
            'count': self.photo_count,
            'photo_sizes': '1',
            'extended': '1',
            'access_token': VkGetPhotos.TOKEN,
            'v': '5.131'
        }
        res = requests.get(VkGetPhotos.URL + URL_METHOD, params=params).json()
        pprint(res)
        urls_list = self._get_photos_info(res, self.photo_count)
        return urls_list


class YaUploader:
    URL = 'https://cloud-api.yandex.net'

    def __init__(self, ya_token):
        self.token = ya_token

    def upload_photos(self, photos_urls_list):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'OAuth {self.token}'
        }
        requests.put(YaUploader.URL + '/v1/disk/resources', headers=headers,
                     params={'path': 'VK_Photos_backup_Komarov'})
        with open('file_info.json', 'r') as file:
            count = 0
            data = json.load(file)
            for url in photos_urls_list:
                requests.post(YaUploader.URL + '/v1/disk/resources/upload', headers=headers,
                              params={'path': f'VK_Photos_backup_Komarov/{data["info"][count]["file_name"]}',
                                      'url': url})
                count += 1


if __name__ == '__main__':
    user_id = input('Введите id пользователя: ')
    # ya_token = input('Введите токен Яндекс Диска: ')
    a = VkGetPhotos(user_id)
    # b = YaUploader(ya_token)
    #
    # b.upload_photos(a.get_photos())
    a.get_photos()


