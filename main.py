import os
import requests
import shutil
from multiprocessing import Pool
import argparse
import imghdr
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotVisibleException, StaleElementReferenceException
import platform
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class CollectLinks:
    def __init__(self):
        executable = ''

        if platform.system() == 'Windows':
            print('Syteme OS detecté : Windows')
            executable = './chromedriver/chromedriver_win.exe'
        elif platform.system() == 'Linux':
            print('Syteme OS detecté : Linux')
            executable = './chromedriver/chromedriver_linux'
        elif platform.system() == 'Darwin':
            print('Syteme OS detecté : Mac')
            executable = './chromedriver/chromedriver_mac'
        else:
            assert False, 'OS pas reconnu'

        self.browser = webdriver.Chrome(executable)

    def get_scroll(self):
        pos = self.browser.execute_script("return window.pageYOffset;")
        return pos

    def wait_and_click(self, xpath):
        #  Si le click ne marche pas pour X raison, on reclique comme des bourins.
        try:
            w = WebDriverWait(self.browser, 15)
            elem = w.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            elem.click()
        except Exception as e:
            print('hummm... time out des clicks - {}'.format(xpath))
            print('Je refresh...')
            self.browser.refresh()
            time.sleep(2)
            return self.wait_and_click(xpath)

        return elem

    def google(self, keyword, add_url=""):
        self.browser.get("https://www.google.com/search?q={}&source=lnms&tbm=isch{}".format(keyword, add_url))

        time.sleep(1)

        print('Je scrolle...')

        elem = self.browser.find_element_by_tag_name("body")

        for i in range(60):
            elem.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.2)

        try:
            # btn_more = self.browser.find_element(By.XPATH, '//input[@value="결과 더보기"]')
            self.wait_and_click('//div[@id="smbw"]')

            for i in range(60):
                elem.send_keys(Keys.PAGE_DOWN)
                time.sleep(0.2)

        except ElementNotVisibleException:
            pass

        photo_grid_boxes = self.browser.find_elements(By.XPATH, '//div[@class="rg_bx rg_di rg_el ivg-i"]')

        print('Liens en cours de scrapping')

        links = []

        for box in photo_grid_boxes:
            try:
                imgs = box.find_elements(By.TAG_NAME, 'img')

                for img in imgs:
                    src = img.get_attribute("src")
                    if src[0] != 'd':
                        links.append(src)

            except Exception as e:
                print('[Un problème avec Google] {}'.format(e))

        print('Cest fait. Site: {}, mots-clés: {}, Total: {}'.format('google', keyword, len(links)))
        self.browser.close()

        return set(links)

    def naver(self, keyword, add_url=""):
        self.browser.get("https://images.search.yahoo.com/search/images?search&p={}{}".format(keyword, add_url))

        time.sleep(1)

        print('Je scrolle...')

        elem = self.browser.find_element_by_tag_name("body")

        for i in range(60):
            elem.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.2)

        try:
            self.wait_and_click('//button[@class="ygbt more-res"]')

            for i in range(60):
                elem.send_keys(Keys.PAGE_DOWN)
                time.sleep(0.2)

        except ElementNotVisibleException:
            pass

        photo_grid_boxes = self.browser.find_elements(By.XPATH, '//li[@class="ld r0"]')

        print('Liens en cours de scrapping')

        links = []

        for box in photo_grid_boxes:
            try:
                imgs = box.find_elements(By.CLASS_NAME, '_img')

                for img in imgs:
                    src = img.get_attribute("src")
                    if src[0] != 'd':
                        links.append(src)
            except Exception as e:
                print('[un problème avec Yahoo] {}'.format(e))

        print('Cest fait. Site: {}, mots-clés: {}, Total: {}'.format('yahoo', keyword, len(links)))
        self.browser.close()

        return set(links)

    def google_full(self, keyword, add_url=""):
        print('[Images Hautes Résolutions]')

        self.browser.get("https://www.google.co.kr/search?q={}&tbm=isch{}".format(keyword, add_url))
        time.sleep(1)

        elem = self.browser.find_element_by_tag_name("body")

        print('Liens en cours de scrapping')

        self.wait_and_click('//div[@data-ri="0"]')
        time.sleep(1)

        links = []
        count = 1

        last_scroll = 0
        scroll_patience = 0

        while True:
            try:
                imgs = self.browser.find_elements(By.XPATH, '//div[@class="irc_c i8187 immersive-container irc-rcd"]//img[@class="irc_mi"]')

                for img in imgs:
                    src = img.get_attribute('src')

                    if src not in links and src is not None:
                        links.append(src)
                        print('%d: %s'%(count, src))
                        count += 1

            except StaleElementReferenceException:
                # Quand ca stale affiche un message d'erreur
                pass
            except Exception as e:
                print('[un soucis avec Google] {}'.format(e))

            scroll = self.get_scroll()
            if scroll == last_scroll:
                scroll_patience += 1
            else:
                scroll_patience = 0
                last_scroll = scroll

            if scroll_patience >= 30:
                break

            elem.send_keys(Keys.RIGHT)

        links = set(links)

        print('Cest fait. Site: {}, mots-clés: {}, Total: {}'.format('google_full', keyword, len(links)))
        self.browser.close()

        return links

    def naver_full(self, keyword, add_url=""):
        print('[Images en Haute Résolution]')

        self.browser.get("https://images.search.yahoo.com/search/images?search&p={}{}".format(keyword, add_url))
        time.sleep(1)

        elem = self.browser.find_element_by_tag_name("body")

        print('Lien en cours de scrapping')

        self.wait_and_click('//div[@class="img_area _item"]')
        time.sleep(1)

        links = []
        count = 1

        last_scroll = 0
        scroll_patience = 0

        while True:
            try:
                imgs = self.browser.find_elements(By.XPATH,
                                                  '//div[@class="image_viewer_wrap _sauImageViewer"]//img[@class="_image_source"]')

                for img in imgs:
                    src = img.get_attribute('src')

                    if src not in links and src is not None:
                        links.append(src)
                        print('%d: %s' % (count, src))
                        count += 1

            except StaleElementReferenceException:
                # Message d'erreur toutca
                pass
            except Exception as e:
                print('[Exception occurred en lançant lappli] {}'.format(e))

            scroll = self.get_scroll()
            if scroll == last_scroll:
                scroll_patience += 1
            else:
                scroll_patience = 0
                last_scroll = scroll

            if scroll_patience >= 30:
                break

            elem.send_keys(Keys.RIGHT)

        links = set(links)

        print('Cest fait. Site: {}, Mots-clés: {}, Total: {}'.format('naver_full', keyword, len(links)))
        self.browser.close()

        return links


if __name__ == '__main__':
    collect = CollectLinks()
    links = collect.naver_full('yahoo')
    print(len(links), links)



class Sites:
    GOOGLE = 1
    NAVER = 2
    GOOGLE_FULL = 3
    NAVER_FULL = 4

    @staticmethod
    def get_text(code):
        if code == Sites.GOOGLE:
            return 'google'
        elif code == Sites.NAVER:
            return 'yahoo'
        elif code == Sites.GOOGLE_FULL:
            return 'google'
        elif code == Sites.NAVER_FULL:
            return 'yahoo'

    @staticmethod
    def get_face_url(code):
        if code == Sites.GOOGLE or Sites.GOOGLE_FULL:
            return "&tbs=itp:face"
        if code == Sites.NAVER or Sites.NAVER_FULL:
            return "&face=1"


class AutoCrawler:
    def __init__(self, skip_already_exist=True, n_threads=4, do_google=True, do_naver=True, download_path='download',
                 full_resolution=False, face=False):
      

        self.skip = skip_already_exist
        self.n_threads = n_threads
        self.do_google = do_google
        self.do_naver = do_naver
        self.download_path = download_path
        self.full_resolution = full_resolution
        self.face = face

        os.makedirs('./{}'.format(self.download_path), exist_ok=True)

    @staticmethod
    def all_dirs(path):
        paths = []
        for dir in os.listdir(path):
            if os.path.isdir(path + '/' + dir):
                paths.append(path + '/' + dir)

        return paths

    @staticmethod
    def all_files(path):
        paths = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if os.path.isfile(path + '/' + file):
                    paths.append(path + '/' + file)

        return paths

    @staticmethod
    def get_extension_from_link(link, default='jpg'):
        splits = str(link).split('.')
        if len(splits) == 0:
            return default
        ext = splits[-1].lower()
        if ext == 'jpg' or ext == 'jpeg':
            return 'jpg'
        elif ext == 'gif':
            return 'gif'
        elif ext == 'png':
            return 'png'
        else:
            return default

    @staticmethod
    def validate_image(path):
        ext = imghdr.what(path)
        if ext == 'jpeg':
            ext = 'jpg'
        return ext  # returns None if not valid

    @staticmethod
    def make_dir(dirname):
        current_path = os.getcwd()
        path = os.path.join(current_path, dirname)
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def get_keywords(keywords_file='keywords.txt'):
        # lire les keys
        with open(keywords_file, 'r', encoding='utf-8-sig') as f:
            text = f.read()
            lines = text.split('\n')
            lines = filter(lambda x: x != '' and x is not None, lines)
            keywords = sorted(set(lines))

        print('{} mots-clés trouvés: {}'.format(len(keywords), keywords))
        input("Assurez-vous d'avoir remplie tous vos mots-clés sur Keyword.txt avec vos mots clés. Appuyez dès lors sur entrer pour lancer le tout :")
        
        # sauvegarder motscles apres sorting
        with open(keywords_file, 'w+', encoding='utf-8') as f:
            for keyword in keywords:
                f.write('{}\n'.format(keyword))

        return keywords

    @staticmethod
    def save_object_to_file(object, file_path):
        try:
            with open('{}'.format(file_path), 'wb') as file:
                shutil.copyfileobj(object.raw, file)
        except Exception as e:
            print('Impossible de sauvegarder - {}'.format(e))

    def download_images(self, keyword, links, site_name):
        self.make_dir('{}/{}'.format(self.download_path, keyword))
        total = len(links)

        for index, link in enumerate(links):
            try:
                print('Téléchargement {} à partir de {}: {} / {}'.format(keyword, site_name, index + 1, total))
                response = requests.get(link, stream=True)
                ext = self.get_extension_from_link(link)

                no_ext_path = '{}/{}/{}_{}'.format(self.download_path, keyword, site_name, str(index).zfill(4))
                path = no_ext_path + '.' + ext
                self.save_object_to_file(response, path)

                del response

                ext2 = self.validate_image(path)
                if ext2 is None:
                    print('Impossible de lire ce fichier - {}'.format(link))
                    os.remove(path)
                else:
                    if ext != ext2:
                        path2 = no_ext_path + '.' + ext2
                        os.rename(path, path2)
                        print('Extension renommée {} -> {}'.format(ext, ext2))

            except Exception as e:
                print('Téléchargement impossible- ', e)
                continue

    def download_from_site(self, keyword, site_code):
        site_name = Sites.get_text(site_code)
        add_url = Sites.get_face_url(site_code) if self.face else ""
        collect = CollectLinks()  # le driver chrome est initialisé à ce niveau

        try:
            print('Liens en cours de chargement {} à partir de {}'.format(keyword, site_name))

            if site_code == Sites.GOOGLE:
                links = collect.google(keyword, add_url)

            elif site_code == Sites.NAVER:
                links = collect.naver(keyword, add_url)

            elif site_code == Sites.GOOGLE_FULL:
                links = collect.google_full(keyword, add_url)

            elif site_code == Sites.NAVER_FULL:
                links = collect.naver_full(keyword, add_url)

            else:
                print('Code du site invalide')
                links = []

            print('Images en cours de téléchargement {} à partir de {}'.format(keyword, site_name))
            self.download_images(keyword, links, site_name)

            print('Done {} : {}'.format(site_name, keyword))

        except Exception as e:
            print('Oupsy {}:{} - {}'.format(site_name, keyword, e))

    def download(self, args):
        self.download_from_site(keyword=args[0], site_code=args[1])

    def do_crawling(self):
        keywords = self.get_keywords()

        tasks = []

        for keyword in keywords:
            dir_name = '{}/{}'.format(self.download_path, keyword)
            if os.path.exists(os.path.join(os.getcwd(), dir_name)) and self.skip:
                print('je saute le dossier existant {}'.format(dir_name))
                continue

            if self.do_google:
                if self.full_resolution:
                    tasks.append([keyword, Sites.GOOGLE_FULL])
                else:
                    tasks.append([keyword, Sites.GOOGLE])

            if self.do_naver:
                if self.full_resolution:
                    tasks.append([keyword, Sites.NAVER_FULL])
                else:
                    tasks.append([keyword, Sites.NAVER])

        pool = Pool(self.n_threads)
        pool.map_async(self.download, tasks)
        pool.close()
        pool.join()
        print('Tâche terminée.')

        self.imbalance_check()

        print('cest fini')

    def imbalance_check(self):
        print('Je check lintégrité des données...')

        dict_num_files = {}

        for dir in self.all_dirs(self.download_path):
            n_files = len(self.all_files(dir))
            dict_num_files[dir] = n_files

        avg = 0
        for dir, n_files in dict_num_files.items():
            avg += n_files / len(dict_num_files)
            print('dir: {}, file_count: {}'.format(dir, n_files))

        dict_too_small = {}

        for dir, n_files in dict_num_files.items():
            if n_files < avg * 0.5:
                dict_too_small[dir] = n_files

        if len(dict_too_small) >= 1:
            for dir, n_files in dict_too_small.items():
                print('Problème de données.')
                print('Je recommande de supprimer les documents présents sur Download en root')
                print('et de retelecharger le tout.')
                print('_________________________________')
                print('Directories trop petites:')
                print('dir: {}, file_count: {}'.format(dir, n_files))

            print("Voulez-vous que je les enlève pour vous? (y/n)")
            answer = input()

            if answer == 'y':
                
                print("En cours de suppression...")
                for dir, n_files in dict_too_small.items():
                    shutil.rmtree(dir)
                    print('supprimé {}'.format(dir))

                print('Quitter ce programme et relancez-le.')
        else:
            print('Aucun problème dintégrité des données.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip', type=str, default='true',
                        help='Skiples mots-clés déjà téléchargés')
    parser.add_argument('--threads', type=int, default=4, help='Nombre de threads à télécharger.')
    parser.add_argument('--google', type=str, default='true', help='Téléchargement de google.com (boolean)')
    parser.add_argument('--naver', type=str, default='false', help='Téléchargement de yahoo.com (boolean)')
    parser.add_argument('--full', type=str, default='true', help='Téléchargement dimages en haute résolution (attention slow)')
    parser.add_argument('--face', type=str, default='false', help='Face search mode')
    args = parser.parse_args()

    _skip = False if str(args.skip).lower() == 'false' else True
    _threads = args.threads
    _google = False if str(args.google).lower() == 'false' else True
    _naver = False if str(args.naver).lower() == 'false' else True
    _full = False if str(args.full).lower() == 'false' else True
    _face = False if str(args.face).lower() == 'false' else True

    # print('Options - les skips:{}, les threads:{}, sur google:{}, sur yahoo:{}, full_resolution ou pas:{}, face:{}'.format(_skip, _threads, _google, _naver, _full, _face))
    print("                                 ▀▄▀▄▀▄ google ιмage daтa collecтor ▄▀▄▀▄▀")
    print("                                              Amine EL OTMANI")
    print ("                                                                         ")
    crawler = AutoCrawler(skip_already_exist=_skip, n_threads=_threads, do_google=_google, do_naver=_naver, full_resolution=_full, face=_face)
    crawler.do_crawling()
