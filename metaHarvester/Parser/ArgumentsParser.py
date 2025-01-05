import datetime
import time
import typing
import itertools
import json
import csv
import argparse
import random
from .RunExamples import *

INTRESTING_FILES = ('.htm', '.xml', '.bak', '.js','.ini', '.sqlite','.sql', '.log', '.backup', '.key', '.csv', '.yml','.json','.db','.sqlite3','.env','.ovpn','.config')
EXTENSIONS = ('.pdf','.doc', '.docx', '.ppt', '.xlsx', '.xls', '.pptx', '.jpg', '.jpeg', '.bmp', '.png', '.tif' )
WAITING_TIME = 30
DOCUMENT_COUNTER = 100
FILESIZE = {'>':1.0}
DEFAULT_DATE = {'>': 315522000.0}

class FileSizeValidator(argparse.Action):
    def converter_size(self,size:int|float,convert_from:str='B'):
        if convert_from == 'B':
            return size
        elif convert_from in ('KB','K'):
            return size*1024
        elif convert_from in ('MB','M'):
            return size*1024*1024
        elif convert_from in ('GB','G'):
            return size*1024*1024*1024
        else:
            raise ValueError('Incorrect value! Use only [B, K, KB, M, MB, G, GB] !')

    def validator(self,size:str,value:str):
        "Проверка данных о размере файла из html страницы"
        if size in ('-',''):
            return None
        if value == '':
            value = 'B'

        try:
            size = int(size)
        except ValueError:
            size = float(size)
        return self.converter_size(size,value)



    def __call__(self, parser, namespace, values, option_string=None): 
        text = {}
        for item in values.split('...'):
            sym = "" # < > =
            num = "" # 10
            val = "" # MB
            for element in item:
                if element in ('>','<','='):
                    sym+=element
                elif element.isdigit() or element == '.':
                    num += f"{element}"
                elif element.isalpha():
                    val+=element
            text[sym] = self.converter_size(float(num),val.upper())
        setattr(namespace, self.dest, text)



class DateValidator(argparse.Action):
    def generate(self,*args,time_format = False):
        if time_format == True:
            symbols = ('-',':')
        else:
            symbols = ('','.','-','/')
        return [f"{x}".join(i) for i in itertools.product(*args) for x in symbols]

    def date_formats(self):
        m = ('%m',r'%b','%B')
        y = ('%Y','%y')
        return self.generate(('%d',),m,y)+self.generate(y,m,('%d',))#[f"{x}".join(i) for i in itertools.product(y,m,('%d',)) for x in symbols]}

    def time_formats(self):
        return self.generate(('%H',),('%M',),('%S',),time_format=True)+self.generate(('%H',),('%M',),time_format=True)#[f"{x}".join(i) for i in itertools.product(('%H',),('%M',)) for x in symbols]}
    
    def parser(self,date:str):
        res = {}
        ranges = date.split('...')
        c = ""
        for r in ranges:
            counter = 0
            for i in range(2):
                if r[i].isdigit():
                    if c == '':
                        c = '=='
                    res[c] = {}
                    break
                c+=r[i]
                counter+=1
            p = r[counter:]
            tmp = p.split('-')
            res[c] = {'date':"","time":""}

            if len(tmp) in (2,4): #если 2020.02.02-12:00 or 2020-02-04-12:00
                res[c]['date'] = "".join(tmp[:-1])
                res[c]['time'] = tmp[-1]
            else:    
                res[c]['date'] = "".join(tmp)
                res[c]['time'] = "00:00"

            c = ""
        return res


    def get_date(self,date:dict) -> typing.Union[datetime.datetime,None]:
        """for date in format
        dd.mm.yyyy with different separated
        
        Args:
            date (_type_): date in string

        Returns:
            _type_: None | str
        """
        for format_item in itertools.product(self.date_formats(),self.time_formats()):
            try:
                return datetime.datetime.strptime(f"{date['date']}-{date['time']}",f"{format_item[0]}-{format_item[1]}")
            except ValueError:
                continue

    def reference(self):
        return """ Available formats:

dd - day.    Format: number from range 1-31
mm - mounth. Format: number from range 1-12, dec, December
yyyy - year. Format: short format 18,19,20 ... , long format 2018,2019...
[yellow bold]Use 24-hours format for time[/yellow bold]

Date:
dd.mm.yyyy      yyyymmdd
dd-mm-yyyy      yyyy.mm.dd
dd/mm/yyyy      yyyy-mm-dd
ddmmyyyy        yyyy/mm/dd
            or 
    unix format date

Compared date:
>={date}    <={date}
>{date}     <{date}
=={date}    {date}

Compared date with time:
{compared date}-12:00:30...{compared date}-14:00:00   Beetwen date1 and date2
{date | compared date}-12:00:00                       Exact match
{compared date}-12:00                                 Earlier or on the specified date
 """


    def __call__(self, parser, namespace, values, option_string=None): 
        info = self.parser(values)
        new_value = {}
        for symbol,value in info.items():
            res = self.get_date(value)
            if res is None:
                raise ValueError('Incorrect date format!\n{}'.format(self.reference()))
            new_value[symbol] = time.mktime(res.timetuple())
        setattr(namespace, self.dest, new_value)

class InsertIntrestingExtensions(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None) -> None:
        setattr(namespace, self.dest, INTRESTING_FILES)

class ReportFormatFile(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None) -> None:
        options = {'-oC':'csv','-oJ':'json','-oT':'txt'}
        if values is not None and values.split('.')[-1] not in options.values():
            raise ValueError('File format not supported! Choose one of these {} formats'.format(list(options.values())))
        setattr(namespace,self.dest,{'filename':values,'format':options[option_string]})

class Target(argparse.Action):
    def read_csv(self,file:str,column:str):
        with open(file,'r',newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            return [row[column] for row in reader]


    def read_json(self,file:str,key:str):
        with open(file,'r') as f:
            content = json.load(f)[key]
            if isinstance(content,list):
                return content
            elif isinstance(content,str):
                return [content]

    
    def read_txt(self,file:str):
        with open(file,'r') as f_txt:
            return f_txt.read().splitlines()

    def readers(self,format:str,*args,ignore_format = False):
        try:
            return {'.csv':self.read_csv,'.json':self.read_json}[format](*args) 
        except KeyError:
            if ignore_format:
                return list(args)
            else:
                raise KeyError('Not corrected input targets file! Use only formats: csv,json or txt. For csv and json choose column with file.json[column]')

    def __call__(self, parser, namespace, values, option_string = None) -> None:
        ignore_format = True if parser.prog.split(' ')[-1] in ('extract','restart') else False
        all_targets = []
        for target in values:
            t = target.split('[')
            if len(t)>1:
                all_targets += self.readers(t[0].split('.')[-1],t[0],t[1][:-1],ignore_format=ignore_format)
            elif t[0].endswith('.txt'):
                all_targets += self.read_txt(t[0])
            else:
                all_targets.append(t[0])
        setattr(namespace,self.dest,all_targets)

class ExtensionConvert(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None) -> None:
        setattr(namespace,self.dest,tuple(map(lambda x:x.replace('.',''),values)))

class DorkValidator(argparse.Action):
    def __call__(self, parser, namespace, values:str, option_string = None) -> None:
        setattr(namespace,self.dest,[values.format_map({'domain':domain}) for domain in namespace.domain])

class PrintHelp(argparse.Action):
    def __call__(self, parser, namespace, values:str, option_string = None) -> None:
        data = {
            None:f'[cyan]{shared_args}[/cyan]',
            'google':f"[#00FF00]{GoogleHelp}[/#00FF00]",
            'index-of':f"[#00FFFF]{IndexOfHelp}[/#00FFFF]",
            'crawler':f"[#FF0000]{CrawlerHelp}[/#FF0000]",
            'dork':f"[#66ffcc]{DorkHelp}[/#66ffcc]",
            'extract':f"[/#ffff99]{ExtractHelp}[/#ffff99]",
            'clear':f"[#33cc33]{ClearHelp}[/#33cc33]",
            'restart': f"[#ffcc66]{RestartHelp}[/#ffcc66]",
            'downloader':f"[#ff0066]{DownloaderHelp}[/#ff0066]",
            'passgen':f"[#99ccff]{PassgenHelp}[/#99ccff]"
            }
        try:
            console.print(data[values])
        except KeyError:
            console.print(f'{values} module not found!',style='red')


def Args():
    target=argparse.ArgumentParser(add_help=False)
    target.add_argument('-t','--targets',dest='domain',help='''
    Input target or targets file.
    Example:https://yandex.ru targets.csv[column name] targets.json[key] targets.txt.
    Or session.json file.
    Or file/catalogs with files of which extract metadata.''',nargs='+',action=Target, required=True)

    files=argparse.ArgumentParser(add_help=False)    
    files.add_argument('-e','--extensions',dest='filetype',help='File extensions',nargs='+',default=EXTENSIONS,action=ExtensionConvert)
    files.add_argument('-s','--size',dest = 'filesize',help='Input filesizes. Example: ">10MB...<20MB" - if filesize after 10MB and before 20MB(beetwen 10MB and 20MB)',default=FILESIZE,action=FileSizeValidator)
        
    full_files = argparse.ArgumentParser(add_help=False)
    full_files.add_argument('--all','--all-files',dest = 'all_files',action='store_true',help='If selected this argument, that will be downloading all files. Ignoring extensions,size and date create.')

    counter_doc = argparse.ArgumentParser(add_help=False)
    counter_doc.add_argument('-c','--count',dest='counter',help='Counter for downloaded documents',default=DOCUMENT_COUNTER,type=int)
    
    report = argparse.ArgumentParser(add_help=False)
    report.add_argument('-oC','-oJ','-oT',dest ='report',help='Report file. oC - Csv file, oJ - Json file, oT - Txt file',action=ReportFormatFile,nargs='?',default={'filename':None,'format':'csv'})

    proxies = argparse.ArgumentParser(add_help=False)
    proxies.add_argument('--tor',dest='tor',help='Using tor network?',action='store_true')
    proxies.add_argument('--proxy',dest='proxy',help='Using proxy? Example: --proxy public - for using public proxy. Or --proxy proxies.txt in format "protocol://user:password@server:port"')

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,description='''A tool for automated document search and metadata extraction from them.\nThis tool uses the latest methods to select documents according to the specified criteria.\nIt uses a double check before downloading a file, checking its size and content type.\nFor some models (e.g. index-of) it also checks the document creation date if it is available.\n''')
    parser.add_argument('-hh','--help-all',dest='help_all',nargs='?',action=PrintHelp)

    modules = parser.add_subparsers(help='Available modules',dest='module')

    #for google
    wait_time = argparse.ArgumentParser(add_help=False)
    wait_time.add_argument('-w','--wait',dest='wait',help='Input waiting time',type=int,default=random.randrange(30,60))

    #for add extension
    intresting_file = argparse.ArgumentParser(add_help=False)
    intresting_file.add_argument('--i','--intresting-files',dest='intresting_files',action=InsertIntrestingExtensions,default=tuple(),help='Add extensions to search for "interesting" files',nargs='?')

    auto_remove = argparse.ArgumentParser(add_help=False)
    auto_remove.add_argument('--auto-remove',dest='auto_remove',help='Removing files after download',action='store_true')


    indexof = modules.add_parser('index-of',description='Search for documents in open directories',help='This module is used to search documents in "Index of" catalogs.',parents=[target,files,counter_doc,proxies,report,full_files,intresting_file,auto_remove])
    indexof.add_argument('-d','--date',dest='last_update',help='Date of the last modification of the document. Example:>=2020-02-23...<2020-02-23-12:00:00',action=DateValidator,default=DEFAULT_DATE)
    google  = modules.add_parser('google',description='Search documents in Google',help='This module is used to search for documents in Google',parents=[target,counter_doc,files,proxies,report,intresting_file,wait_time,auto_remove])
    
    dork    = modules.add_parser('dork',description='Use dorks for search info in Google',help='Input dork or file dorks or domain',parents=[target,wait_time,proxies])
    dork.add_argument('--depth',dest='depth',help='The depth of the search on google pages.By default - 3 pages',type=int,default=3)
    dork.add_argument('--dork',dest='dork',help='Input custom dorks.For add target use this record: site:{domain}',action=DorkValidator,required=False)
    crawler = modules.add_parser('crawler',description='Use this module to crawling of site',help='Input site url or files with sites',parents=[target,files,report,proxies,full_files,counter_doc])
    extract = modules.add_parser('extract',description='Extract metadata from local files',help='Use this module to extract metadata from local files',parents=[target,report,auto_remove])
    restart = modules.add_parser('restart',description='Restart Session',help='Input report with saved session',parents=[target])
    download= modules.add_parser('downloader',description='Downloading files.Does not extract metadata from files!',parents=[target],help='Use this module for downloading files from internet.')
    clear   = modules.add_parser('clear',description='Clear metadata from documents',parents=[target],help='Use this module for clear documents.')
    passget = modules.add_parser('passgen',description="Generator passwords",help='Use this module for generate passwords',parents=[target])
    
    return parser.parse_args()