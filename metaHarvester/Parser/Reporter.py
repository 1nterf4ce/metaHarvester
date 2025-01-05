import csv
import json
from typing import Any, Iterable,Callable
from Utils.Colors import info
import os

def ShowSaveInfo(func):
    "отображать информацию о сохранении файла при каждом вызове функции"
    def inner(*args,**kwargs):
        info(f"Report: {args[0].folder_name}/{args[1]} saved!")
        try:
            return func(*args,**kwargs)
        except UnicodeEncodeError:
            ...
    return inner

class Report:
    def __init__(self,domain:str):
        self.folder_name = os.path.join(domain,'reports')
        self.columns = {'pdf':['filename', 'Creator', 'Producer', 'CreationDate','ModDate'],
                        'tif':['filename', 'Model','Make', 'GPSInfo', 'DateTime','ResolutionUnit', 'XResolution', 'YResolution', 'YCbCrPositioning', 'ExifOffset','Software', 'Orientation'],
                        'jpg':['filename', 'Model','Make', 'GPSInfo', 'DateTime','ResolutionUnit', 'XResolution', 'YResolution', 'YCbCrPositioning', 'ExifOffset','Software', 'Orientation'],
                        'jpeg':['filename', 'Model','Make', 'GPSInfo','DateTime','ResolutionUnit', 'XResolution', 'YResolution', 'YCbCrPositioning', 'ExifOffset','Software', 'Orientation'],
                        'bmp':['filename', 'Model','Make', 'GPSInfo', 'DateTime','ResolutionUnit', 'XResolution', 'YResolution', 'YCbCrPositioning', 'ExifOffset','Software', 'Orientation'],
                        'png':['filename', 'Model','Make', 'GPSInfo', 'DateTime','ResolutionUnit', 'XResolution', 'YResolution', 'YCbCrPositioning', 'ExifOffset','Software', 'Orientation'],
                        'doc':['filename','codepage','author', 'title', 'last_saved_by', 
                                'total_edit_time', 'create_time', 'last_saved_time', 
                                'company', 'last_printed', 'creating_application'],
                        'xls':['filename','codepage','author', 'title', 'last_saved_by', 
                                'total_edit_time', 'create_time', 'last_saved_time', 
                                'company', 'last_printed', 'creating_application'],
                        'ppt':['filename','codepage','author', 'title', 'last_saved_by', 
                                'total_edit_time', 'create_time', 'last_saved_time', 
                                'company', 'last_printed', 'creating_application'],
                        'docx':['filename','creator', 'last_modify', 'date_create', 'date_modify','email','number'],
                        'xlsx':['filename','creator', 'last_modify', 'date_create', 'date_modify','email','number'],
                        'pptx':['filename','creator', 'last_modify', 'date_create', 'date_modify','email','number']}

        try:
            os.makedirs(self.folder_name)
        except FileExistsError: ...


    @ShowSaveInfo
    def CsvFormat(self,filename:str,content:list[dict]|dict,*args,**kwargs):
        'передать дополнительным аргументом filetype=pdf, чтобы указать расширение файла, для выбора колонок для записи'
        with open(os.path.join(self.folder_name,filename),'w',encoding='utf-8',newline='') as csv_writer:
            writer = csv.DictWriter(csv_writer,fieldnames=self.columns[kwargs['filetype']])
            writer.writeheader()
            for element in content:
                writer.writerow(dict(map(lambda x:(x,element.get(x)),self.columns[kwargs['filetype']])))
            # writer.writerows(content) if isinstance(content,list) else writer.writerow(content)

    @ShowSaveInfo
    def JsonFormat(self,filename:str,content:list[dict],*args,**kwargs):
        with open(os.path.join(self.folder_name,filename),'w',encoding='utf-8') as js_file_w:
            json.dump(content,js_file_w,ensure_ascii=False,indent=4)

    @ShowSaveInfo
    def TxtFormat(self,filename:str,content:str|list[dict],*args,**kwargs) -> None:
        "Запись в текстовый формат"
        with open(os.path.join(self.folder_name,filename),'w',encoding='utf-8') as f:
            f.write(content)

    def define_format(self,format:str) -> Callable:
        return {'csv':self.CsvFormat,'json':self.JsonFormat,'txt':self.TxtFormat}[format]
