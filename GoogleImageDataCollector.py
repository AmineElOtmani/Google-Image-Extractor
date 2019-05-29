import os
import requests
import shutil
from multiprocessing import Pool
import argparse
from scrap_links import CollectLinks
import imghdr


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
        
        # sauvegarder mots-cles apres sorting
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
    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip', type=str, default='true',
                        help='Skip les mots-clés déjà téléchargés')
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
