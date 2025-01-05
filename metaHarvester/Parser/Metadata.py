import pikepdf
from datetime import datetime
import os
from Utils.Colors import critical,info,log_info,console
import re
from PIL import Image
from PIL.ExifTags import TAGS
from .OleFile import OleFileIO,NotOleFileError
import typing
import zipfile
from bs4 import BeautifulSoup
from enum import Enum
from contextlib import suppress
from .Reporter import Report
from Utils.GetTimeNow import today
import mimesis
import shutil

class Pattern(Enum):
    number: str = re.compile(r'([+]{0,1}\d{1,3}\(\d{3,4}\)(-\d{1,3}){3})|(?<=\s{1})([+]?\b\d{11}\b)|(\d{1}(-\d{2}){2})')
    email:  str = re.compile(r'(?:[Aa-zZ0-9\.\'_-]+@[Aa-zZ]+\.[Aa-zZ]+)')
    

class Remover:
    def generate_random_data(self,max_length:int=20):
        return os.urandom(max_length)
    
    def rename_file(self,file:str):
        new_filename = os.path.split(file)
        new_path = os.path.join(new_filename[0],self.generate_random_data().hex())
        os.rename(file,new_path)
        return new_path
    

    def erase_content(self,file:str):
        with open(file,'wb') as f:
            f.write(self.generate_random_data())
        return file
    
    
    def rm(self,file:str):        
        os.remove(self.rename_file(self.erase_content(file)))
        log_info(f'{file}: deleted.')


class Metadata:
    users = []
    def add_user(self,user):
        if user not in self.users:
            self.users.append(user)
            console.print('\n')
            info(f'Found user: [#ff0000  italic]{user}[/#ff0000 italic]')

    def fix_datetime(self,document_date:str):
        if document_date.startswith('D:'):
            try:
                _date,offset = document_date[2:].split('+')
                return datetime.strftime(datetime.strptime(_date,'%Y%m%d%H%M%S'),'%d-%m-%Y %H:%M:%S')+' +'+re.sub(r'[\'\"]',':',offset)[:-1]
            except ValueError:
                return datetime.strftime(datetime.strptime(document_date[2:-1],'%Y%m%d%H%M%S'),'%d-%m-%Y %H:%M:%S')
        return document_date
    
    def extract_date_and_time(self,date_str:str) -> str:
        return re.sub('[A-Z]+',' ',date_str)[:-1]

    def extract_pdf(self,filepath:str) -> tuple[dict,list,str]:
        " for pdf files"
        result = {}
        fieldnames = set()
        try:
            with pikepdf.Pdf.open(filepath) as meta:
                for key,value in meta.docinfo.items():
                    if key[1:] == 'Author':
                        self.add_user(str(value))
                    
                    fieldnames.add(key[1:])
                    result[key[1:]] = self.fix_datetime(str(value))
            fieldnames.add('filename')
        except:
            pass
        return {"filename":os.path.basename(filepath)}|result

    def extract_pictures(self,filepath:str) -> tuple[dict,list,str]:
        "for images"
        result = {}
        fieldnames = set()
        img = Image.open(filepath)
        exif_data = img.getexif()
        for tag in exif_data:
            data = exif_data.get(tag)
            if isinstance(data,bytes):
                continue
            else:
                tagname = TAGS.get(tag,tag)
                fieldnames.add(tagname)
                result[tagname] = str(data)
        fieldnames.add('filename')
        img.close()
        return {"filename":os.path.basename(filepath)}|result

    def validator_metainfo(self,value:typing.Any,encoding:str='utf-8'):
        if isinstance(value,bytes):
            try:
                return value.decode(encoding=encoding)
            except UnicodeDecodeError:
                return str(value)
        elif isinstance(value,list):
            for item in value:
                return self.validator_metainfo(item,encoding=encoding)
        else:
            return value

    def extract_doc(self,filename:str) -> tuple[dict,list,str]:
        items = ['codepage','author', 'title', 'last_saved_by', 
                 'total_edit_time', 'create_time', 'last_saved_time', 
                'company', 'last_printed', 'creating_application']
        result = {}
        codepage='utf-8'
        try:
            with OleFileIO(filename) as doc:
                # personal_info = self.check_personal_info(doc.openstream('worddocument').read().decode('utf-16','ignore')) #check encode for document
                x = doc.get_metadata()
                for i in items:
                    data = getattr(x,i)
                    if i == 'codepage':
                        if  data is not None and data > 0:
                            codepage = f"{data}"
                    if i in ('author','last_saved_by'):
                        self.add_user(self.validator_metainfo(data,encoding=codepage)) if data is not None else None
                    result[i] = self.validator_metainfo(data,encoding=codepage)
            return {"filename":os.path.basename(filename)}|result
        except NotOleFileError:
            critical(f'Error in document format: {filename}')
            return {},[],'DOC'
    def extract_docx(self,filename:str) -> tuple[dict,list,str]:
        result = {}
        attrs = {'creator':'dc:creator','last_modify':'cp:lastModifiedBy','date_create':'dcterms:created','date_modify':"dcterms:modified"}
        with zipfile.ZipFile(filename,'r') as zip_zip:
            with zip_zip.open('word/document.xml','r') as f:
                doc_content = BeautifulSoup(f.read(),'xml')
                persona = self.check_personal_info(doc_content.text)
            with zip_zip.open('docProps/core.xml','r') as core:
                soup = BeautifulSoup(core.read(),'xml')
                for key_name, doc_tag in attrs.items():
                    with suppress(AttributeError):
                        if key_name in ('creator','last_modify'):
                            self.add_user(soup.find(doc_tag).text)
                        result[key_name] = self.extract_date_and_time(soup.find(doc_tag).text) if 'date' in key_name else soup.find(doc_tag).text
        return {"filename":os.path.basename(filename)}|result|persona
    
    def check_personal_info(self,content:str) -> dict:
        "поиск номеров и email адресов"
        result = {}
        for pattern in [Pattern.email,Pattern.number]:
            val = re.findall(pattern.value,content)
            x = [z for y in val for z in y if z and len(z)>3 ]
            result[pattern.name] = x
            if x:
                info('Found {}:\n{}'.format(pattern.name,str(f"\n{' '*15}".join(x))))
        return result


    def Metaparser(self,filename:str|None) -> dict:
        if filename is  None:
            return 
        if filename.endswith('.pdf'):
            return self.extract_pdf(filename)
        elif filename.endswith(('.tif','.jpg','.jpeg','.bmp','.png')):
            return self.extract_pictures(filename)
        
        elif filename.endswith(('.doc','.xls','.ppt')):
            return self.extract_doc(filename)
        
        elif filename.endswith(('.docx','.xlsx','.pptx')):
            return self.extract_docx(filename)

class Extract(Metadata,Remover):
    alias='extract'
    def __init__(self,domain:list,report:dict,auto_remove:bool) -> None:
        self.files           = domain
        self.report_format   = report['format'] if report['format'] != 'csv' else 'json'
        self.report_filename = report['filename'] if report['filename'] is not None else today(filename=True)
        self.auto_remove     = auto_remove


    def extract_from_file(self,filepath:str):
        "Извлечь метаданные из файлов"
        res = self.Metaparser(filepath)
        if self.auto_remove == True:
            self.rm(filepath)
        return res

    def recursive_search_file(self,path,files:list)->list[tuple[str,str]]:
        'Функция для рекурсивного поиска файлов в указанных папках.Альтернатива os.walk()'
        for item in os.listdir(path):
            new_item=os.path.join(path,item)
            if os.path.isdir(new_item):
                self.recursive_search_file(new_item,files = files)
            else:
                files.append(self.extract_from_file(new_item))


    def go(self):
        report = Report('local').define_format(self.report_format)
        result = []
        for target in self.files:
            if os.path.exists(target):
                if os.path.isdir(target):
                    self.recursive_search_file(target,files=result)
                else:
                    result.append(self.extract_from_file(target,report))
            else:
                critical(f'{target} Not Found!')
                return
        report(f'{self.report_filename}.{self.report_format}',result)
        report('users.txt',"\n".join(self.users))
        info('Found users:\n{}'.format("\n".join(self.users)))

class Clear(Extract):
    alias='clear'
    def __init__(self, domain: list) -> None:
        self.target = domain

    def fake_data(self,parametr:str) -> dict:
        return {'user':mimesis.Person(locale=mimesis.Locale.EN).full_name(),'date':mimesis.Datetime().date(start=1980).strftime('%d-%m-%Y'),'datetime':f"{mimesis.Datetime().date(start=1980).strftime('%Y-%m-%d')}T{mimesis.Datetime().time().strftime('%H:%M:%S')}Z"}[parametr]
    def define_format_and_clear_meta(self,file:str):
        if file.endswith('.pdf'):
            with pikepdf.open(file,allow_overwriting_input=True) as pdf_file:
                with pdf_file.open_metadata() as metadata:
                    metadata['dc:author'] = self.fake_data('user')
                    metadata['dc:creator'] = self.fake_data('user')
                    metadata['dc:CreationDate'] = self.fake_data('date')
                    metadata['dc:ModDate'] = self.fake_data('date')
                pdf_file.save(file)
            info(f'{file} - Modified!')
            return
        elif file.endswith(('.tif','.jpg','.jpeg','.bmp','.png')):
            with Image.open(file) as img:
                # Копирование изображения без метаданных
                new_img = img.copy()
                new_img.info.clear()

            new_img.save(file)#,{"jpg":"JPEG",'jpeg':'JPEG','png':"PNG",}[file.split('.')[-1]])
            info(f'{file} - Modified!')
            return
        elif file.endswith(('.doc','.xls','.ppt')):
            try:
                with OleFileIO(file) as ole:
                    stream = ole.openstream('SummaryInformation')
                    stream.setvalue(b'\x00' * stream.size)
                    ole.save('output.doc')
                info(f'{file} - Modified!')
            except NotOleFileError:
                critical(f"Error format for file: {file}")
            return
        elif file.endswith(('.docx','.xlsx','.pptx')): 
            attrs = {'user':'dc:creator','user':'cp:lastModifiedBy','datetime':'dcterms:created','datetime':"dcterms:modified"}
            short_filename = 'temp'
            h = file
            try:
                os.mkdir(short_filename)
            except FileExistsError:
                shutil.rmtree(short_filename)
                os.mkdir(short_filename)

            with zipfile.ZipFile(file,'r') as zip_zip:
                zip_zip.extractall(short_filename)
                            
            with open(os.path.join(short_filename,'docProps','core.xml'),'rb') as core:
                try:
                    soup = BeautifulSoup(core.read().decode('utf-8','ignore'),'xml')
                except UnicodeDecodeError:
                    critical(f'Document encode not supported!')
                    return
                for key_name, doc_tag in attrs.items():
                    with suppress(AttributeError):
                        new = soup.find(doc_tag)
                        new.string = self.fake_data(key_name)
                        soup.find(doc_tag).replace_with(new)
                with open(os.path.join(short_filename,'docProps','core.xml'),'w') as sf:
                    sf.write(str(soup))
            with zipfile.ZipFile(file,'w',compresslevel=9,allowZip64=True) as z2:
                for folder,_,files in os.walk(short_filename):
                    for file in files:
                        z2.write(os.path.join(folder,file),os.path.relpath(os.path.join(folder,file),os.path.basename(short_filename)).replace('../',''))
            shutil.rmtree(short_filename)
            info(f'{h} - Modified!')
            return 



    def extract_from_file(self, filepath: str, executor_function):
        try:
            return executor_function(filepath)
        except UnicodeDecodeError:
            return

    def go(self):
        for target in self.target:
            if os.path.exists(target):
                if os.path.isdir(target):
                    self.recursive_search_file(target,report_function_address=self.define_format_and_clear_meta)
                else:
                    self.extract_from_file(target,self.define_format_and_clear_meta)
            else:
                critical(f'{target} Not Found!')
                return