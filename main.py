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
        with open('file_info.json', 'a') as file:
            file.write(str(photo_info_dict_list))
        return urls_list

    def get_photos(self):
        URL_METHOD = 'photos.get'
        album_id = input('Введите id скачиваемого альбома: ')
        photo_count = int(input('Введите кол-во скачиваемых фотографий: '))
        params = {
            'owner_id': self._get_user_id(),
            'album_id': album_id,
            'count': photo_count,
            'photo_sizes': '1',
            'extended': '1',
            'access_token': VkGetPhotos.TOKEN,
            'v': '5.131'
        }
        res = requests.get(VkGetPhotos.URL + URL_METHOD, params=params).json()
        urls_list = self._get_photos_info(res, photo_count)


class YaUpload:
    def __init__(self, ya_token):
        self.token = ya_token


if __name__ == '__main__':
    a = VkGetPhotos('begemot_korovin')
    a.get_photos()
