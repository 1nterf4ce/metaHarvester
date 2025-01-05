import io
import re
from itertools import starmap
from typing import Iterator

import requests
from bs4 import BeautifulSoup

from .PathToSave import FileSave
from Utils.RandomUser import user_agent
from Utils.Colors import info,debug,critical
from Utils.Domain import GetDomain
from .Restarter import Sessions
from .Metadata import Pattern
from .Reporter import Report

class Crawler(FileSave):
    alias = 'crawler'
    def __init__(self, domain: list,filetype:list,all_files:bool,filesize:dict,report:dict,counter:int,tor: bool = False, proxy: str | None = None) -> None:
        self.domains         = domain #Домены
        self.file_extensions = tuple(filetype) #расширения файлов
        self.full_file       = all_files #Скачивать все файлы? Если True - размер файлов будет игнорироваться
        self.filesize        = filesize #Размер файла
        self.tor             = tor #Сеть tor
        self.proxy           = proxy #Через прокси
        self.report          = report
        self.counter         = counter
        #отключить csv формат
        if self.report['format'] == 'csv':
            self.report['format'] = 'json'

    @property
    def set_headers(self)->dict:
        'Установить заголовки запроса'
        proxy=None
        if self.proxy is not None: #Проверка,что указаны прокси
            proxy=self.PrivateProxyParser(self.proxy) #список приватных прокси.использовать с функцией PrivateProxyParser и рандом
        if self.tor: #Проверка,что указана сеть Tor
            proxy={'socks5':'socks5://127.0.0.1:9050','socks5':'socks5://127.0.0.1:9050'} #Передать в переменную self.proxy прокси адреса сети Tor
        return {'headers':{'user-agent':user_agent()},'proxies':proxy}

    def clear_values(self,*args):   
        'Удалить пустые элементы из кортежей'
        for arg in args:
            if arg:
                return re.sub(r'\s+','',arg)
 
    def phone(self,text:BeautifulSoup)->Iterator:
        'Поиск телефонных номеров.Вернёт итератор'
        #((?:[\+0-9]{2,3}|[0-9]?)\s(?:\([0-9]{3,6}\))\s?(?:[0-9-\s?]+)+) - 8 (42224) 6 - 25 - 25 или +8 (42224) 6 - 25 - 25
        #(?:\d{11}\s{,1})|(\+\d{11}) - 89276311232 или +89276311232 
        return starmap(self.clear_values,re.findall(r'((?:[\+0-9]{2,3}|[0-9]?)\s(?:\([0-9]{3,6}\))\s?(?:[0-9-\s?]+)+)|(?:\d{11}\s{,1})|(\+\d{11})',text))

    def emails(self,text:BeautifulSoup)->list:
        "Поиск email адресов"
        return re.findall(r'(?:[a-zA-Z0-9\.\'_-]+@[a-zA-Z\.]+)',text)

    def Robots(self,domain):
        'загрузить файл robots.txt в буффер'
        res=requests.get(f"{domain}/robots.txt",**self.set_headers)
        info('Found file robots.txt')
        with io.StringIO() as buffer:
            for r in res.iter_content(8192):
                buffer.write(r.decode())
            return buffer.getvalue()

    #-----------   Сортировка найденных Url адресов    -----------
    def create_new_link(self,url:str,link:str)->str|None:
        'Сортировка ссылок' 
        values=[link.startswith('/'),url.endswith('/')]
        if all(values):
            return url+link[1:]
        elif link.startswith('http') and not link.endswith(self.file_extensions):
            return link
        elif any(values):
            return url+link
        elif not all(values):
            return f'{url}/{link}'
        return url

    def replacer_url(self,found_urls:list[str],domain:str) -> list:
        """Удаление ссылок:
        1.Не связанных с доменом [http]
        2.Ведущих на главную страницу[./, /, index.php ...]
        3.Ссылки со всплывающем окном [#]
        Args:
            found_urls (list): = список отфильтрованных ссылок
            domain (str):  = домен
        Returns:
            (list):[http://url,/url] """
        bad_urls=('#','mailto','tel:','/','#','./','index.php','home.php','index.html','homepage.php','homepage.html','home.html','',domain) #domain - домашняя страница 
        return [found_url for found_url in found_urls if  not found_url.startswith(bad_urls[:6]) and found_url not in bad_urls]

    def url_filter(self,html:BeautifulSoup,domain:str)->list[str]:
        "Удалить Url адреса,не связанные с доменом,домашние страницы и ссылки на другие документы"
        return self.replacer_url(filter(lambda z:
                                re.findall(fr'[http|https]+?:\/\/(?={domain})',z) or not z.startswith('http'), # Получить все ссылки в которых есть протокол://домен или /page 
                                map(lambda h:h.get('href',''),html.find_all('a'))),domain)
                            
    def find_input_frame(self,html:BeautifulSoup) -> list:
        'Поиск полей для ввода'
        return [{s.name:s.attrs} for s in html.find_all('input')]

    def Set_Protocol(self,domain:str) -> str:
        'Определение протокола для подключения к сайту.  domain (str):Домен сайта'
        if domain.startswith(('https://','http://')):
            return domain
        else:
            try:
                r=requests.get('http://'+domain,timeout=10,**self.set_headers,allow_redirects=True)
                [info("{:12}: {}".format(key,r.headers.get(key,''))) for key in ('Server','X-Powered-By')]
                return r.url
            except (requests.exceptions.ConnectionError,requests.exceptions.ConnectTimeout):
                return

    def extract_documents_links(self,link:str) -> bool:
        return True if link.startswith(('http://','https://')) and link.endswith(self.file_extensions) else False

    def _get_files(self,intresting_files:dict[str,list],report:Report,documents):
        report.JsonFormat('intresting.json',intresting_files)

        result = self.Downloading(documents[:self.counter],folder=None,max_filesize=self.filesize)
        content = []
        while True:
            try:
                res = next(result)                        
                if res is None: #если скачивает все документы с сайта, то из некоторых типов файлов не возможно извлечь метаданные
                    continue 
                content.append(res)
            except StopIteration:
                break
            
        info('Found users:\n{}'.format('\n'.join(self.users)))
        filename = f"{self.report['filename']}_" if self.report['filename'] is not None else ".{}".format(self.report['format'])
        report.define_format(self.report['format'])(f"report{filename}",content)
        report.TxtFormat('users.txt','\n'.join(self.users))
        self.users.clear()
        documents.clear()



    def go(self,cache:list = [],links:list = []) -> None:
        'Рекурсивный поиск по всему сайту'#['application/pdf','application/msword','image/jpeg','image/png','image/tiff']
        for link in self.domains:
            cache = cache #ссылки,с которых собрана информация
            links = links

            intresting = {x:[] for x in (Pattern.email.name,Pattern.number.name,'errors','input')} #для номеров телефонов, email, страницы с полями для ввода и страницы с ошибками ответа сервера

            #определить домен
            domain = GetDomain(link)
            
            url = self.Set_Protocol(domain) #Определить протокол сайта

            if url is None:
                critical(f'{domain} - Not available!')
                continue

            info(self.Robots(url))
            report = Report(domain)
            counter = 0
            documents = []
            try:
                self.Crawling(url,
                              domain=domain,
                              cache=cache,
                              intresting=intresting,
                              links=links,
                              last_url=url,
                              counter = counter,
                              documents = documents)
                
            except KeyboardInterrupt:
                Sessions(self.__init__).save({'cache':cache,'links':links,'domain':domain},filename=f"session-crawler-{domain}.json")

            except IndexError:
                self._get_files(intresting,report,documents)
                continue
            self._get_files(intresting,report,documents)
        


    def Crawling(self,
                 url:str,
                 domain:str,
                 counter, #счётчик документов
                 cache:list,
                 documents:list,
                 intresting:dict[str,list],
                 links:list = [],
                 last_url="") -> None:
        """Рекурсивный поиск по сайту

        Args:
            url (str): Ссылка на сайт
            domain (str): Домен сайта. (ссылка без протокола)
            cache (list):  Список посещённых страниц
            input_frames (dict):  словарь для найденных полей ввода текста.  ключ - ссылка на страницу, значение - html селектор
            errors (list):  список для ссылок с ошибочным ответом сервера
            filename (str):  имя файла для отчёта
            links (list, optional): . Defaults to []. список для ссылок на документы
            last_url (str, optional): . Defaults to "". последняя ссылка (протокол+домен сайта)
        """
        cache.append(url)
        try:
            request_on_site = requests.get(url,**self.set_headers,timeout=3)
            if request_on_site.status_code==200:
                debug(f'[200] {url.strip()}')
                soup=BeautifulSoup(request_on_site.text,'lxml')
                soup_text = soup.text

                intresting[Pattern.email.name] += re.findall(Pattern.email.value,soup_text) 
                intresting[Pattern.number.name]+= re.findall(Pattern.number.value,soup_text)
                intresting['input'].append({url:self.find_input_frame(soup)}) if self.find_input_frame(soup) else None

                #Поиск ссылок на странице
                all_links = self.url_filter(html=soup,domain=domain)
                documents += [link for link in all_links if all((link.startswith(('http://','https://')),link.endswith(self.file_extensions),link not in documents))]
                if len(documents) >= self.counter:
                    raise IndexError


                links_2 = [self.create_new_link(url=last_url,link=y) for y in all_links if y not in documents]
                for page in links_2:
                    if page in cache:
                        continue
                    self.Crawling(url=page,
                                  domain=domain,
                                  cache=cache,
                                  intresting=intresting,
                                  counter=counter,
                                  documents=documents,
                                  links=links,
                                  last_url=last_url)
                last_url = url
            else:
                critical(f'[{request_on_site.status_code}] {url}')
                intresting['error'].append(url)
        except (requests.exceptions.ConnectTimeout,requests.exceptions.ReadTimeout,requests.exceptions.ConnectionError):
            critical(f'{url} - Connection Error!')
            intresting['error'].append(url)
            return