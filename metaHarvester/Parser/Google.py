import os
import random
import re
from time import sleep
from contextlib import suppress
from itertools import repeat

import requests
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup

from Utils.Colors import console,info,debug,warning,critical,custom_style
from Utils.Domain import GetDomain
from Utils.RandomUser import user_agent
from .PathToSave import FileSave
from .Restarter import Sessions
from .Reporter import Report
from Utils.GetCookies import get_cookie

class Google(FileSave,Report):
    alias = 'google'
    def __init__(self,domain:list,filetype:list,counter:int,wait:int|float,filesize:dict,report:str,intresting_files:bool,auto_remove:bool,tor:bool=False,proxy:str|None=None) -> None:
        """Определение параметров парсера
        Args:
            domain (str): Домен сайта
            headers (dict): Заголовки запроса,user-agent 
            cookies (dict): Куки
            count (int):  количество скачиваемых документов
            wait(int | float): задержка между запросами
            filesize (dict): Размер файла.Формат записи >10<15 [больше 10Mb,но меньше 15Mb]
            tor (bool, optional): Defaults to False. = Использование сети Tor [True | False]
            proxy (str | None, optional):  Defaults to None. = файл с приватными прокси адресами 
        Одновременное использование сети Tor и прокси НЕ ПОДДЕРЖИВАЕТСЯ!"""
        super(FileSave).__init__()
        self.domains            = domain #Домен сайта
        self.file_extensions    = filetype
        self.count              = counter #Количество документов
        self.wait               = wait #Время ожидания между запросами        
        self.filesize           = filesize #Словарь
        self.intresting_files   = intresting_files
        self.auto_remove        = auto_remove #удаление файлов после скачивания
        self.tor                = tor #сеть tor
        self.proxy              = proxy #Приватные прокси
        self.report             = report
        # self.public_proxy=self.PublicProxy() #публичные прокси
        if self.proxy is not None: #Проверка,что указаны прокси
            self.proxy=self.PrivateProxyParser(proxy) #список приватных прокси.использовать с функцией PrivateProxyParser и рандом
        if self.tor: #Проверка,что указана сеть Tor
            self.proxy={'socks5':'socks5://127.0.0.1:9050','socks5':'socks5://127.0.0.1:9050'} #Передать в переменную self.proxy прокси адреса сети Tor
        
    def go(self,cache:list = [],documents = [],extension = None,count_docs:int = 0):
        cache = cache #Список для посещённых страниц
        cookies = get_cookie()
        documents = documents
        doc_count = count_docs
        flag = False
        exts = self.file_extensions
        for item in self.domains:
            console.rule(f'[bold #33ccff]{item}[/bold #33ccff]')
            domain = GetDomain(item)
            #для возобновлённой сессии
            if flag == False and extension is not None:
                flag = True
                for index,var  in enumerate(self.file_extensions):
                    if var == extension:
                        break
                    exts = self.file_extensions[index:]
            for extension in exts:
                folder = self.Create_Folders(domain,extension) #Создать папки для каждого типа документов
                debug(f'Search {extension} documents...')
                url=f'https://www.google.com/search?q=filetype%3A{extension}+site%3A{domain}&start=0'
                try:
                    self.GoogleParser(url,page_cache=cache,documents=documents,cookie=cookies,domain = domain,folder = folder,doc_counter = doc_count)
                except KeyboardInterrupt:
                    Sessions(self.__init__).save({'cache':cache,'documents':documents,'extension':extension,"count_docs":doc_count,'domain':domain},filename=f'session-google-{domain}.json')
            self.TxtFormat(f'Users-{domain}.txt',"\n".join(self.users))
            self.users.clear()

    def GoogleParser(self,url:str,page_cache:list,documents:list,cookie:dict,domain:str,folder:str,doc_counter:int,number:int=0):
        """Парсинг выдачи Google
        Args:
            url (str): ссылка
            document_links (set): множество для найденных документов.Чтоб не добавлять одинаковые 
            folder (str): Папка,в которую скачать документы
            number (int, optional):  Defaults to 0. Счётчик для страниц"""
        if url not in page_cache:
            try:
                page_cache.append(url)
                r=requests.get(url,headers={'user-agent':user_agent()},cookies=cookie,proxies=self.proxy)#Новые заголовки и прокси на каждый запрос
            except ConnectionError as ce:
                return  ce #Ошибка при подключении
            else:
                status=r.status_code
                if status==200:
                    debug(f"[{status}] Page {number//10}\t{url}")
                    soup=BeautifulSoup(r.text,'lxml') #Передать в функции
                    x=soup.find_all('a')
                    links=[j.get('href') for j in x if domain in j.get('href','') ] #Сохранить только те ссылки,в которых есть домен
                    document_links=list(set(self.get_documents_links(links,domain))) #Документы
                    #Добавить в список найденные документы,если их нет в списке
                    if document_links:#Скачивание документов
                        new_document_list = document_links
                        if doc_counter + len(document_links)>self.count:
                            new_document_list = document_links[:(self.count - doc_counter)]
                        downloaded_documents = self.Downloading(new_document_list,folder=folder,max_filesize=self.filesize,remove=self.auto_remove)
                        while True:
                            try:
                                dow_doc = next(downloaded_documents)
                                if dow_doc is None:
                                    doc_counter-=1
                                    continue
                                doc_counter+=1
                                info(f"{doc_counter}/{self.count} documents...")
                                self.define_format(self.report['format'])(f"{dow_doc[-1]}-{domain}.{self.report['format']}",*dow_doc[:-1])
                                if doc_counter == self.count:
                                    return
                            except StopIteration:
                                break

                        
                    else: #Если документов нет - выйти из цикла
                        critical('Documents not found!')
                        return               

                    if self.check_hidden_page(links): #Скрытая страница
                        info('Found hidden page!')
                        url+='&filter=0'
                    elif self.check_next_page(links): #следующая страница
                        number+=10
                        url=self.generate_page_number(url,number=number)
                    #Продолжить рекурсивный поиск документов
                    self.timer(self.wait)
                    self.GoogleParser(url,number=number,page_cache=page_cache,documents=documents,cookie=cookie,domain=domain,folder=folder,doc_counter=doc_counter)
                #Проверка на капчу
                elif status==429:
                    self.Captcha()()
                #Проверка на другие коды ошибок
                else:
                    critical(f"[{status}]")
                    return
                
    def timer(self,waiting_time:int):
        'задержка между запросами'
        wait_time = random.randrange(waiting_time)
        with console.status(f'[italic #33ccff]Waiting {wait_time} seconds...[/italic #33ccff]',spinner='point',spinner_style=custom_style) as status:
            for i in range(wait_time):
                status.update(f'[italic #33ccff]Waiting {wait_time-i} seconds...[/italic #33ccff]',spinner_style=custom_style)
                sleep(1)


    def get_value(func)->list:
        def wrapper(*args):
            if len(args)>1:
                return list(filter(lambda x: x is not None,map(func,args[0],repeat(args[1]))))
            else:
                return list(filter(lambda x: x is not None,map(func,args[0])))

        return wrapper
    def generate_page_number(self,url:str,number:int)->str:
        """Генерировать ссылки с номерами страниц,добавляя +10(number) в параметр ссылки &start=number
        Args:
            url (str): Ссылка
            number (int): Номер страницы
        Returns: str"""
        return re.sub(r'&start=\d*',f'&start={number}',url)
    #Поиск элементов на странице
    @staticmethod
    @get_value
    def check_hidden_page(text:str)->str|None:
        'Поиск ссылки на скрытую страницу'
        with suppress(AttributeError):
            return re.fullmatch(r'(\/search[\W\S]+&filter=0\b)',text).group()

    @staticmethod
    @get_value
    def get_documents_links(text:str,domain:str)->str|None:
        """Получить ссылки на документы
        Args:
            text (str):  список всех ссылок со страницы
        Returns: str|None: """
        if text.startswith((f'http://{domain}',f'https://{domain}')):
            return text

    @staticmethod
    @get_value
    def check_next_page(text:str)->str:
        "найти все ссылки в списке,в которых есть параметр start"
        if 'start' in text:
            return text
    # --------------------------------   Captcha   ----------------------------------------------
    def Captcha(self):
        "Если получена капча"
        critical('[429] Captcha!')
        continue_function  = {
            'Continue with private proxy':self.continue_with_private_proxy, #Продолжить через приватные прокси
            'Continue with tor networks':self.continue_with_tor_network, #продолжить через сеть Tor
            'Continue with public proxy':self.continue_with_public_proxy, #Продолжить через публичные прокси
            'Save configuration':self.save_config, #Сохранить конфигурацию,чтобы продолжить в другое время
            'Exit':exit} #Выйти
 
        #Удалить пункты продолжить через приватные прокси или сеть Tor
        if self.proxy is not None:
            del continue_function['Continue with private proxy']
        if self.tor:
            del continue_function['Continue with tor networks']
        k = continue_function.keys()
        t = {}
        for index,value in enumerate(k):
            console.print(f"{index}. {value}",style='green')
            t[index] = value
            #Выбранное действие
        opt=self.select_option(k)
        return continue_function[t[opt]]
        
    def select_option(self,value:list) -> int:
        """Выбрать действие при капчеss
        Args:
            value (list): список ,из которого нужно выбрать элемент
        Raises:
            ValueError: Если индекс элемента не входит в массив с длинной списка или введено не число
        Returns:
                int"""
        try:
            selection_option=int(input('Select option: '))
            if selection_option not in range(len(value)):
                raise ValueError
            return selection_option
        except ValueError:
            warning('Input number!')
            return self.select_option(value)


    def continue_with_public_proxy(self):
        "Продолжить через публичные прокси"
        proxy_list=self.PublicProxy()
        self.proxy=self.PrivateProxyParser(proxy_list,public=True)


    def continue_with_private_proxy(self):
        path=input('Path for private proxy file:')
        if os.path.exists(path)==True:
            private_proxy_list=self.PrivateProxy()
            self.proxy=self.PrivateProxyParser(private_proxy_list)
            return
        else:
            critical('Incorrected path!')
            self.continue_with_private_proxy()


    def continue_with_tor_network(self):
        'Продолжить через сеть Tor'
        self.proxy={'socks5':'socks5://127.0.0.1:9050','socks5':'socks5://127.0.0.1:9050'}
        return

    def save_config(self):
        raise KeyboardInterrupt
