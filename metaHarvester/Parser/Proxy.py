import random
import requests
from bs4 import BeautifulSoup
from Utils.RandomUser import user_agent
from Utils.Colors import critical
class Proxy:
    def PublicProxy(self):
        r = requests.get('https://hidemy.name/ru/proxy-list/?type=5#list',headers={'user-agent':user_agent()})
        if r.status_code == 403:
            critical(f"Public proxy not accessed!\n[{r.status_code}] - https://hidemy.name/ru/proxy-list/?type=5#list")
            exit()
        soup = BeautifulSoup(r.text,'lxml')
        table = soup.find('table').find('tbody').find_all('tr')
        return [f"{y[0]}:{y[1]}"  for x in table for y in   x.find_all('td')[:2]]

    def PrivateProxy(self,file:str):
        with open(file,'r',encoding='utf-8') as private_proxy:
            return private_proxy.readlines()
        
    def PrivateProxyParser(self,proxies:list,public=False):
        return random.choice(proxies)

