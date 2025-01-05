import os
from Utils.Colors import critical,info,warning,debug
import re
import string
class PassGen:
    def __init__(self,domain:list):
        self.targets = domain

    @property
    def replaced_symbols(self):
        return {1:'l',2:'z','3':'e',4:'h',5:'s',6:'b',7:'t',8:"B",9:'g',0:"o"}

    def replace_symbol_register(self,symbol:str,action="lower"):
        if action == 'lower':
            return symbol.lower()
        return symbol.upper()

    def mix_symbols_in_nickname(self,username:str) -> list:
        "For usernames"
        result = []
        result+=[username.lower(),username.upper(),username.capitalize()]
        for register_variant in ('lower','upper'):
            tmp = ""
            for symbol in username:
                try:
                    tmp+=self.replace_symbol_register(self.replaced_symbols[int(symbol)])
                except ValueError:
                    tmp+=self.replace_symbol_register(symbol,register_variant)
            result.append(tmp)
        for register_variant in ('lower','upper'):
            tmp = ''
            for symbol in username:
                if isinstance(symbol,int):
                    tmp+=f"{symbol}"
                else:
                    tmp+=self.replace_symbol_register(symbol,register_variant)
            result.append(tmp)
        return result

    def mix_username(self,username:list):
        "Для полных имён пользователей,где есть фамилия,имя и отчество"
        result = []
        result+=[''.join(username).upper(),''.join(username).lower()]
        if len(username)==3:
            result.append(f"{username[0]}.{username[1][0]}.{username[2][0]}")
            result.append(f"{username[1][0]}.{username[2][0]}.{username[0]}")
            for year in range(1900,2023):
                #year after name
                result.append(f"{username[1][0]}.{username[2][0]}.{username[0]}{year}")
                result.append(f"{username[0]}.{username[1][0]}.{username[2][0]}{year}")
                #year before name
                result.append(f"{year}{username[1][0]}.{username[2][0]}.{username[0]}")
                result.append(f"{year}{username[0]}.{username[1][0]}.{username[2][0]}")
                #name beetwen years
                result.append(f"{year}{username[1][0]}.{username[2][0]}.{username[0]}{year}")
                result.append(f"{year}{username[0]}.{username[1][0]}.{username[2][0]}{year}")
                result.append(f"{username[1]}{year}")
                result.append(f"{year}{username[1]}{year}")
                result.append(f"{username[1]}")
        elif len(username) == 2:
            result.append(f"{username[1][0]}.{username[0]}")
            result.append(f"{username[0]}.{username[1][0]}")

            for year in range(1900,2023):
                result.append(f"{year}{username[1][0]}.{username[0]}{year}")
                result.append(f"{year}{username[0]}.{username[1][0]}{year}")

                result.append(f"{year}{username[1][0]}.{username[0]}")
                result.append(f"{year}{username[0]}.{username[1][0]}")

                result.append(f"{username[1][0]}.{username[0]}{year}")
                result.append(f"{username[0]}.{username[1][0]}{year}")

                result.append(f"{username[0]}{year}")
                result.append(f"{year}{username[0]}{year}")
                result.append(f"{username[0]}")

        else:
            result+=self.mix_symbols_in_nickname(username[0])
        return result


    def check_existst_folder(self,folder:str,counter:int=0) -> str:
        if os.path.exists(folder) == True:
            counter +=1
            return self.check_existst_folder(f"{folder.split('-')[0]}-{counter}",counter=counter)
        else:
            os.mkdir(folder)
            return folder


    def go(self):
        folder = self.check_existst_folder("Passwords")
        for item in self.targets:
            if not item:continue

            path = os.path.join(folder,re.sub(f'[{string.punctuation}]','',item)+'.txt')

            content = set(self.mix_username(item.split(' ')))
            with open(path,'w') as password_file:
                password_file.write("\n".join(content))
            info(f'Passwords generated in [bold]{path}[/bold]')
