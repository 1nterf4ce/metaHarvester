import os
import json
import csv

import requests
import urllib.parse
from concurrent.futures import ThreadPoolExecutor,as_completed
from rich.progress import Progress, BarColumn, DownloadColumn, TextColumn,TaskID,TotalFileSizeColumn,FileSizeColumn

from .DocumentInfo import FileInfo
from .Proxy import Proxy
from typing import Union,Iterable,Iterator
from .Metadata import Metadata,Remover
from Utils.Domain import GetDomain
from itertools import repeat

class Explorer:
    def __init__(self) -> None:
        pass
    
    def check_filename(self,filename:str,counter:int=0):
        if os.path.exists(filename): #file exists
            filename = "copy_{}_{}".format(counter,filename)
            counter +=1
            self.check_filename(filename,counter=counter)
        return filename    


    def SaveInJson(self,filename:str,content:dict):
        filename = self.check_filename(filename)
        with open(filename,'w') as f:
            json.dump(content,f,ensure_ascii=False,indent=4)

    def SaveInCsv(self,filename,content:list[dict],fieldnames):
        filename = self.check_filename(filename)
        with open(filename,'w',newline='') as csv_file:
            writer = csv.DictWriter(csv_file,fieldnames=fieldnames)
            writer.writeheader()
            for item in content:
                writer.writerow(item)
            

    def SaveInTXT(self,filename:str,content:list):
        with open(filename,'w') as f:
            f.write("\n".join(content))


class FileSave(FileInfo,Proxy,Metadata,Remover):
    alias='downloader'
    def __init__(self,domain = None,output_folder = "result") -> None:
        super(Proxy).__init__()
        self.targets = domain
        self.output = output_folder

    def define_filename(self,url:str):
        try:
            return urllib.parse.unquote(url.rsplit('/',1)[-1])
        except UnicodeDecodeError:
            return 'undefined_name.{}'.format(url.split('.')[-1])

    def set_folder(self,folder:str,filename:str):
        return os.path.join(folder,filename.split('.')[-1])

    def check_filesize(self,length:int|None,max_filesize:dict)->bool:
        if length is None:
            return False
        else:
            return any(self.compare_values(max_filesize,int(length)))


    def Downloading(self,urls:Union[Iterable,list,tuple],folder:str|None,max_filesize:dict,remove:bool = False,not_extract_metadata = False) -> Iterator:
        # Create a progress bar
        func = self.Metaparser if not_extract_metadata == False else print

        with Progress(TextColumn("{task.description}"), 
                            BarColumn(),
                            DownloadColumn(),
                            TextColumn("[bold red] {task.fields[server]}"),transient=True) as progress:

            # Start downloading the files using ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=20) as pool:
                futures = pool.map(self._download, urls, repeat(folder),repeat(progress),repeat(max_filesize))
                for future in futures:
                    if future is not None:
                        result = func(future)
                        if remove:
                            self.rm(future)         
                        yield result

    def _download(self, url, folder:str|None, progress:Progress, max_filesize:dict):
        # Download the file using requests.get()
        response = requests.get(url,headers={'user-agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'},proxies=None,stream=True)
        try:
            length = int(response.headers.get('Content-Length'))
        except (ValueError,TypeError):
            length = None
        if self.check_filesize(length,max_filesize): #проверка по размеру файла,если он не указан на странице
            server = self.get_server_headers(response.headers)
            filename = self.define_filename(url)
            folder = self.Create_Folders(GetDomain(url),filename.split('.')[-1]) if folder is None else folder
            task=progress.add_task(start=False,description=f"[cyan]Downloading {filename}[/cyan]",total=length,server = server["Server"])
            progress.start_task(task)
            path = os.path.join(folder,filename)
            downloaded_bytes = 0
            with open(path, "wb") as file:
                for data in  response.iter_content(chunk_size=8192):
                    file.write(data)
                    downloaded_bytes+=len(data)
                    progress.update(task,completed=downloaded_bytes)
            return  path

    def Create_Folders(self,path:str,extension:str):
        new_path = os.path.join(path,extension)
        try:
            os.makedirs(new_path)
        except FileExistsError:
            ...
        finally:
            return new_path


    def go(self):
        [item for item in self.Downloading(self.targets,self.output,{">":1.0})]