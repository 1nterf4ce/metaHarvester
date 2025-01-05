import operator
from functools import partial

class FileInfo:
    def bytes_to_megabytes(self,value:int|float)->int|float:
        """Перевести размер из байтов в мегабайты для дальнейшего сравнения
        Args:
            value (int | float): размер скачиваемого файла.получить из заголовков
        Returns:
            int|float: Мегабайты"""
        return value/1024/1024


    def compare_values(self,values:dict,value:int|float|None) -> list[bool]|list[bool,bool]:
        """Сравнить значения 
        >>> c.compare_values({'>': 1644670260.0, '<': 1652358120.0},1652358125)
            [True, True, False, False]
        Args:
            values (dict): словарь из Parse_args
            value (int | float): Сравниваемое значение.Получить из заголовков ответа
        Return list[bool]: True | False Если одно сравниваемое значение
                list[bool,bool] Если в аргументах переданы 2 сравниваемых значения.Пример,>10<15"""
        if value is None:
            return [False]
        operands={'<':operator.lt,'<=':operator.le,'>':operator.gt,'>=':operator.ge,"==":operator.eq}
        if len(values)==1:
            return [operands.get(operand)(value,v) for operand,v in values.items()]
                
        else:
            functions,arguments=[],[] #Функция и аргументы для сравнения значений
            for func_name,func_argument in values.items():
                functions.append(operands.get(func_name))
                arguments.append((value,func_argument))
            return list(map(lambda x,y: partial(x,*y)(),functions,arguments)) #Вызов функции и получение её результата
            # return list(chain(*[list(k) for k in map(lambda x: starmap(x,arguments),functions)]))

    def get_server_headers(self,server_response:dict)->dict|None:
        """Получение заголовков ответа сервера. [application,image]
        Return dict(Server: str, Size: int) | None"""
        response_type=server_response.get('Content-Type','').split('/')[0]
        if response_type in ('application','image'):
            return {'Server':server_response.get('Server','Not defined!'),'Size':int(server_response.get('Content-Length',0))}
        return {"Server":"Not defined!",'Size':0}