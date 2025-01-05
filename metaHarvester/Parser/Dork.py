import requests
from bs4 import BeautifulSoup
from Utils.Colors import debug,info,warning,critical,console
from Utils.GetCookies import get_cookie
from Utils.RandomUser import user_agent
from Utils.Domain import GetDomain
from Utils.GetTimeNow import today
from .ArgumentsParser import INTRESTING_FILES
from .Google import Google
from .Restarter import Sessions
from .Reporter import Report
import re

class Dork(Google):
    alias = 'dork'
    def __init__(self,domain:list,depth:int,wait:int,proxy:str|None|list,tor:bool,dork:list|None) -> None:
        self.targets = domain
        self.depth   = depth
        self.wait    = wait
        self.proxy   = proxy
        self.tor     = tor
        self.dork    = dork

    def to_string(separator:str='.'):
        def inner(func):
            def wrapper(*args,**kwargs):
                return separator.join(func(*args,**kwargs))
            return wrapper
        return inner
    
    @to_string(separator='.')
    def get_main_domain(self,target:str):
        spl = target.split('.')
        if spl[-2] not in ('edu','gov','mil') or len(spl)>=3:
            return spl[-2:]
        return spl[-3:]

    @property
    def all_options(self) -> dict[str|list[str]]:
        return {'Enumerate subdomains':["site:*.{}"],
                'Find intresting files':["site:{} filetype:{}"],
                'Find admin panel':['site:{} intitle:(admin | Admin | login | Login | Signin)','site:{} intext:Вход',"site:{} intitle:Вход",'site:{} intext:Login','site:{} inurl:/login',"site:{} inurl:(wp-login | wp-admin)"],
                'Find vulnerable url parameters':["site:{} inurl:*.php?id=",'site:{} inurl:*.php?page=','site:{} inurl:*.php?uid=']}


    def get_selected_options(self,option:dict[str,list]) -> list:
        info('Select option/options:')
        for index,item in enumerate(option):
            console.print("{}. [#aaff99]{}[/#aaff99]".format(index,item))
        while True:
            try:
                options = set(map(int,console.input('[cyan]Enumerate options separated by space: [/cyan]').split(' ')))
            except ValueError:
                critical('Input only numbers!')
                continue
            else:
                if not all([x in range(len(option)) for x in options]):
                    critical('Number not in range!')
                    continue
                return list(options)

    def go(self,options:list|None = None,cache:list = [],page_number:int = 0,mode:str="w"):
        cookie = get_cookie()
        if self.dork:
            for dork_item in self.dork:
                urls = []
                console.rule(dork_item)
                cache = cache
                mode = mode
                try:
                    self.Dorker(f"https://www.google.com/search?q={dork_item}&start=0",cookie=cookie,module='',cache=cache,urls=urls,page_number=page_number,filemode=mode)
                except KeyboardInterrupt:
                    Sessions(self.__init__).save({'cache':cache,'options':None,'domain':dork_item,'mode':mode},filename=f'session-dork-custom.json')
            return

        elif options is None:
            options = self.get_selected_options(self.all_options)

        values = {x:y for x,y in enumerate(self.all_options)}
        for target in self.targets:
            cache = cache
            mode=mode
            extracted_domain = GetDomain(target)
            console.rule(target)
            for element in options:
                urls = []
                try:
                    dork_category_title = values[element]
                    info(dork_category_title)
                    if dork_category_title == 'Enumerate subdomains':
                        extracted_domain = self.get_main_domain(extracted_domain)
                    for url in self.all_options[dork_category_title]:
                        if dork_category_title == 'Find intresting files':
                            for extension in INTRESTING_FILES:
                                self.Dorker(f"https://www.google.com/search?q={url.format(extracted_domain,extension[1:])}&start=0",cookie=cookie,module=dork_category_title,cache=cache,urls=urls,page_number=page_number,filemode=mode)
                        else:
                            self.Dorker(f"https://www.google.com/search?q={url.format(extracted_domain)}&start=0",cookie=cookie,module=dork_category_title,cache=cache,urls=urls,page_number=page_number,filemode=mode)
                except KeyboardInterrupt:
                    Sessions(self.__init__).save({'cache':cache,'options':options,'domain':target,'mode':mode},filename=f'session-dork-{extracted_domain}.json')


    def Dorker(self,url:str,cookie:dict,cache:list,urls:list,page_number:int,page_counter:int=0,module:str='',exclude_domains:str ="",filemode:str='a'):
        if page_counter == self.depth:
            if module == 'Enumerate subdomains': #убрать найденные домены из списка
                info('Found subdomains:')
                [console.print(f"[#00FF00]{i}[/#00FF00]") for i in urls]
                self.TxtFormat(f'subdomains-{GetDomain(url)}.txt',"\n".join(urls),mode=filemode)
            else:
                text = re.sub('Find','Found',module)
                info(text) if text is not None else info('Result for scanning for custom dorks!')                    

                [console.print(f"[#00FF00]{i}[/#00FF00]") for i in urls]
                filename = f'{module.split(" ")[1] if len(module.split(" "))>1 else "custom-dork"}.txt'
                self.TxtFormat(filename,"\n".join(urls),mode=filemode)
                info(f'Result saved in {filename}')
            return
        debug(url)
        if url not in cache:
            r = requests.get(url,headers={'user-agent':user_agent()},cookies=cookie)
            self.timer(self.wait)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text,'lxml')
                if module == 'Enumerate subdomains': #убрать найденные домены из списка
                    urls+=[n for n in set(map(GetDomain,
                        filter(
                            lambda x:all((x.startswith('http'),'google' not in x, not x.startswith('/'))),            
                                map(lambda link:link.get('href',''),soup.find_all('a')
                                    )
                                )
                        )
                        ) if n not in urls]    
                    console.print('\n')
                    exclude_domains+=" -site:"+" -site:".join(map(GetDomain,urls))
                    url=re.sub('&start=',f"{exclude_domains}&start=",url)
                else:
                    urls+=[item for item in filter(
                            lambda x:all((x.startswith('http'),'google' not in x, not x.startswith('/'))),            
                                map(lambda link:link.get('href',''),soup.find_all('a')
                                    )
                                ) if item not in urls]
                page_counter+=1
                if self.check_hidden_page(urls): #Скрытая страница
                    info('Found hidden page!')
                    url+='&filter=0'
                else:#if self.check_next_page(urls): #следующая страница
                    page_number+=10
                    url=self.generate_page_number(url,number=page_number)

                self.Dorker(url,cookie=cookie,cache=cache,urls=urls,page_counter=page_counter,module=module,exclude_domains=exclude_domains,page_number=page_number)
            elif r.status_code == 429:
                self.Captcha()()
            else:
                critical(f"[{r.status_code}] - {url}")
        cache.append(url)
        