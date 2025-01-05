import requests
from bs4 import BeautifulSoup
from time import mktime
import re
import os
from .PathToSave import FileSave
from Utils.Colors import console,info,debug,warning,critical
from Utils.RandomUser import user_agent
from Utils.Domain import GetDomain
from contextlib import suppress
from .ArgumentsParser import DateValidator,FileSizeValidator
from .Reporter import Report
from .Restarter import Sessions
from Utils.GetTimeNow import today


class IndexOf(FileSave,DateValidator,FileSizeValidator):
    alias = 'index-of'
    def __init__(self,domain:list,filetype:list|tuple,filesize:dict,counter:int,tor:bool,proxy:dict|None,report:dict,intresting_files:list|tuple,auto_remove:bool,last_update:dict,all_files:bool) -> None:
        self.domains         = domain
        self.file_extensions = filetype
        self.filesize        = filesize
        self.counter         = counter
        self.tor             = tor
        self.proxy           = proxy
        self.report          = report
        self.intresting      = intresting_files
        self.auto_remove     = auto_remove
        self.last_data       = last_update
        self.all_files       = all_files
        self.captcha         = False

    def _get_files(self,files_list:dict[str,list],report_object:Report,folder:str) -> None:
        debug('All files founded! Begin downloading ...')
        #скачивание файлов
        for ext,found_files in files_list.items():
            debug(f'Downloading {ext} files ...')
            report_filename = f"{self.report['filename']}_" if self.report['filename'] is not None else ".{}".format(self.report['format']) 

            downloaded_documents = self.Downloading( #скачает и проанализирует файл
                found_files,
                folder=os.path.join(folder,ext),
                max_filesize=self.filesize,
                remove=self.auto_remove)
            content = []
            while True:
                try:
                    content.append(next(downloaded_documents))
                except StopIteration:
                    report_object.define_format(self.report['format'])(f"{ext}{report_filename}",content,filetype=ext)
                    break

        info('Found users:\n{}'.format('\n'.join(self.users)))
        report_object.TxtFormat('users.txt','\n'.join(self.users))
        
    def go(self):
        for domain in self.domains:
            main_domain = GetDomain(domain)
            self.strong_check  = True #Если True  - то будет проверять по дате и размеру файла c html страницы

            console.rule(f'[bold #33ccff]{main_domain}[/bold #33ccff]')
            debug('Creating folders...')
            documents = {}
            [(documents.update({extension.replace('.',''):[]}),self.Create_Folders(main_domain,extension.replace('.',''))) for extension in self.file_extensions+self.intresting] #Создать папки для каждого типа документов
            report = Report(main_domain)

            try:
                self.RecursiveIndexOf(domain,documents,next_domain = True,domain=main_domain,show_info=True)
            except KeyboardInterrupt:
                Sessions(self.__init__).save(variables={"domain":main_domain},filename=f'index-of-{main_domain}.json')
            except IndexError:
                self._get_files(documents,report,main_domain)
                documents.clear()
                continue
            self._get_files(documents,report,main_domain)
            documents.clear()
            self.users.clear()

    def RecursiveIndexOf(self,url:str,documents:list,next_domain:bool = False,domain:str = '',show_info = False):
        """Рекурсивный поиск в открытых директориях

        Args:
            url (str): Url Link
            documents (list): _description_
            next_domain (bool, optional): _description_. Defaults to False.
            domain (str, optional): _description_. Defaults to ''.
            show_info (bool, optional): _description_. Defaults to False.
        """
        info(url)

        if next_domain:
            url,soup = self.define_protocol(url)
            if url is None: #если хост не доступен
                return 
            if self.check_index_of_directory(soup,show_info=show_info) == False: #if link not in "index of"  
                #search open dir in google
                warning("Open Directory not found in {}".format(url))
                if self.captcha == False:
                    debug(f"Search for open directories for {domain} in Google...")
                    link_to_open_dirs = self.search_open_dir_in_Google(domain) #check only first page
                    if not link_to_open_dirs:
                        critical(f'{domain}: Open directories not found!')
                        return
                    else:
                        not_dublicated = []
                        for x in link_to_open_dirs:
                            res = re.search(fr"http[s]?:\/\/([Aa-zZ0-9-\.]+)?{domain}\/[Aa-zZ0-9-\.]+\/",x)
                            if res is None:
                                continue
                            if res.group(0) not in not_dublicated:
                                not_dublicated.append(res.group(0)) 
                        for link in not_dublicated:
                            self.RecursiveIndexOf(url=link,documents=documents,domain=domain)

        else:
            try:
                req  = requests.get(url,headers={'user-agent':user_agent()}, proxies=self.proxy)
            except (requests.exceptions.ConnectionError,requests.exceptions.ChunkedEncodingError):
                return
            else:
                soup = BeautifulSoup(req.text,'lxml')
                if self.check_index_of_directory(soup,show_info=show_info) == False: #if link not in open dir
                    return

        content = self.extract_documents(self.define_html_markup(soup,url=url),documents)
        while True:
            try:
                rq = next(content)
            except StopIteration:
                break
            else:
                self.RecursiveIndexOf(rq,documents=documents,domain=domain)


    def extract_documents(self,items:list[dict],files:list):
        if items is None:
            return
        for item in items:
            if not item['filename']:
                continue

            if item['filename'].endswith('/'):
                yield item['url']
            # print(self.validator(*re.findall('([\d+\.]+|-)([A-Z])?',item['size'])[0]))# print(item['filename'],"{}, '{}'".format(mktime(self.get_date(item).timetuple()),self.validator(*re.findall('([\d+\.]+|-)([A-Z])?',item['size'])[0])),self.compare_values(self.last_data,mktime(self.get_date(item).timetuple()))+self.compare_values(self.filesize,self.validator(*re.findall('([\d+\.]+|-)([A-Z])?',item['size'])[0])))
            #проверить,если уже найдено достаточное количество документов для каждого из расширений файлов
            if all(map(lambda x: len(x) == self.counter,files.values())):
                raise IndexError


            for file in self.correct_filename(item):
                list_documents = files[file.split('.')[-1]] #список документов для определённого расширения файла
                if len(list_documents) == self.counter:
                    continue
                else:
                    list_documents.append(file)

    
    
    def checker_fileinfo_from_html_page(self,result:dict):
        if self.strong_check == False:
            return [result['url']]
        else:
            if all(self.compare_values(self.last_data,mktime(self.get_date(result).timetuple()))+self.compare_values(self.filesize,self.validator(*re.findall(r'([\d+\.]+|-)([A-Z])?',result['size'])[0]))):
                return [result['url']]
            return []


    def correct_filename(self,result:dict[str,str]) -> list:
        if result['url'].endswith(self.intresting) or result['url'].endswith(self.file_extensions) or self.all_files == True:
            return self.checker_fileinfo_from_html_page(result)
        else:
            return []


    def search_open_dir_in_Google(self,domain) -> set:
        domain = GetDomain(domain)
        r = requests.get(f'https://www.google.com/search?q=site%3A{domain} intitle%3A"Index of"',headers={'user-agent':user_agent()},proxies = self.proxy)
        if r.status_code == 429:
            critical(f'Captcha!')
            self.captcha = True
            return None
        soup = BeautifulSoup(r.text,'lxml')
        hrefs = set(x.group(0) for x in map(lambda x:re.search(fr'http[s]?:\/\/([Aa-zZ0-9-\.]+)?{domain}(\/\S*)?',x.get('href','')),soup.find_all("a")) if x and '/&' not in x.group(0))
        return hrefs
     
    def define_protocol(self,domain:str,protocol=('http://','https://'),index=-1)->BeautifulSoup:
        if not domain.startswith('http'):
            domain = f'http://{domain}'
        r = requests.get(domain,headers={'user-agent':user_agent()},proxies=self.proxy,allow_redirects=True)
        debug(f'Defined site protocol: {r.url}')
        return r.url,BeautifulSoup(r.text,'lxml')

    def check_index_of_directory(self,content:BeautifulSoup,show_info:bool = True):
        "Проверить,что это открытая директория"
        title = content.find('h1')
        if not title:
            return False
        if title.text.startswith('Index of'):
            if show_info == True:
                with suppress(AttributeError):
                    info(f"Server: {content.find('address').text}")
            return True
        return False
    
    def check_pwd(self,content:str,url:str):
        "перейти в корень сайта"
        s = content.split('/')

    @property
    def keys(self):
        return ('filename','date','time','size')

    def define_html_markup(self,soup:BeautifulSoup,url:str) -> list[dict]|None:
        funcs = (self.table_tag,self.pre_tag,self.ul_tag)
        if not url.endswith('/'):
            url+='/'
        for func in funcs:
            try:
                res = func(soup,url)
            except AttributeError:
                continue
            else:
                if res:
                    return res


    def table_tag(self,soup:BeautifulSoup,url:str) -> list[dict]:
        "if html markup used 'table' tags fir show content"
        table = soup.find('table')
        if not table:
            return
        result = []
        content = table.find_all('tr')[3:-1]
        #check open directory has files
        if not content:
            critical(f'{url} - Files not found.')
            return 

        for x in content:
            td = x.find_all('td')[1:-1]
            #define document link
            link = url+td[0].find('a').get('href') 

            #define fileinfo            
            items = re.split(r'\s+',' '.join(item.text for item in td))
            result.append(dict(zip(self.keys,items))|{"url":link})
        return result

    def pre_tag(self,soup:BeautifulSoup,url:str) -> list[dict]:
        "if html markup used 'pre' tags for show content"
        return [dict(zip(self.keys,[item.text]+re.split(r'\s+',item.next_sibling.text)[1:-1]))|{"url":url+item.get('href')} for item in soup.find('pre').find_all('a')[5:]]

    def ul_tag(self,soup:BeautifulSoup,url:str) -> list[dict]:
        "If html markup used 'ul' tags for show content"
        self.strong_check = False
        return [dict(zip(self.keys,[item.find('a').text,0,0,'-']))|{"url":url+item.find('a').get('href')} for item in soup.find('ul').find_all('li')[1:]]