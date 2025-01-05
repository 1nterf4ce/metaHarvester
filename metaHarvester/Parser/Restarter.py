import json
import ast
import inspect
from argparse import Namespace
from Utils.GetTimeNow import today
from Utils.Colors import debug
from contextlib import suppress

class Sessions(ast.NodeVisitor):
    def __init__(self,class_address) -> None:
        self.class_address = class_address
        self.init_body = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> dict:
        args = [arg.arg for arg in node.args.args[1:]] #аргументы функции init
        for body in node.body:
            if isinstance(body,ast.Assign):
                item = None
                if isinstance(body.value,ast.Name):
                    item = body.value.id

                elif isinstance(body.value,ast.Call):
                    try:
                        item = body.value.args[0].id
                    except IndexError:
                        pass
                if item in args:
                    self.init_body[body.targets[0].attr] = item
        return 

    def get_init_arguments(self,node:ast.FunctionDef):
        _class_address = node.__self__
        node = ast.parse(f"class {_class_address.__class__.__name__}:\n{inspect.getsource(node)}")
        for item in ast.iter_child_nodes(node):
            self.visit(item)
        result = {}
        for key,val in self.init_body.items():
            result[val] = getattr(_class_address,key)
        return result|{"module":getattr(_class_address,'alias')} #insert in class object attribute "alias" = alias from argparser

    def save(self,variables:dict,filename:str|None=None):
        """можно указать добавить ключ domain в variables со значением на текущий сканируемый домен,чтобы удалить уже просканированные домены при возобновлении сессии 
         в классе,сессия которого будет сохранена, нужно добавить аттрибут alias с именем модуля для возобновления сессии(alias указывается из списка модулей,
         например, для модуля google алиасом будет google, для dork будет dork и т.д)
        alias example:
        Class Dork:
            alias = 'dork'"""
        init_args = self.get_init_arguments(self.class_address)
        if filename is None:
            filename = f"session-{today(filename=True)}.json" 
        if len(init_args['domain']) > 1:
            for item in init_args['domain']:
                if item == variables.get('domain'):
                    break
                init_args['domain'].remove(item)
        #удаление ключа с текущим доменом из сканирования
        with suppress(KeyError):
            del variables['domain']

        with open(filename,'w',encoding='utf-8') as f:
            json.dump(init_args|{"cache_args":variables},f,ensure_ascii=False,indent=4)
        debug(f'Session saved in {filename}')    
        exit()

class Restart:
    alias = 'restart'
    def __init__(self,domain:list) -> None:
        self.session = domain

    def go(self):
        with open(self.session[0],'r',encoding='utf-8') as f:
            return Namespace(**json.load(f))
