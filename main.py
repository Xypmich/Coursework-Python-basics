import json
import requests
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
    URL = 'fb.do'


if __name__ == '__main__':
    vk_photos_list = VkGetPhotos()
    ya_photos_uploader = YaUploader()
    social = input('Введите название соцсети (VK - Вконтакте, OK - Одноклассники, INST - Инстаграм): ').lower()
    cloud = input('Введите название облачного хранилища (YA - Яндекс Диск, GD - Google Drive): ').lower()
    user_command = social + cloud
    while user_command != 'exit':
        if user_command == 'vkya':
            vk_user_screen_name = input('Введите id пользователя: ')
            ya_user_token = input('Введите токен Яндекс Диска: ')
            user_command = ya_photos_uploader.upload_photos(vk_photos_list.get_photos(vk_user_screen_name),
                                                            ya_user_token)
        if user_command == 'another_action':
            social = input('Введите название соцсети (VK - Вконтакте, OK - Одноклассники, INST - Инстаграм): ').lower()
            cloud = input('Введите название облачного хранилища (YA - Яндекс Диск, GD - Google Drive): ').lower()
            user_command = social + cloud
    print('Работа программы завершена.')
