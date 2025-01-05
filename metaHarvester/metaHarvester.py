from Parser.ArgumentsParser import Args
from Parser.PathToSave import FileSave
from Parser.IndexOf import IndexOf
from Parser.Google import Google
from Parser.Metadata import Extract,Clear
from Parser.PathToSave import FileSave
from Parser.Crawl import Crawler
from Parser.Restarter import Restart
from Parser.Dork import Dork
from Parser.Passgen import PassGen
def main(args):
    var:dict = vars(args)
    del var['help_all']
    if var['module'] is None:return
    cache = var.pop('cache_args',{})
    class_obj = {'index-of':IndexOf,'google':Google,'downloader':FileSave,'extract':Extract,'crawler':Crawler,'restart':Restart,'clear':Clear,'dork':Dork,'passgen':PassGen}[var.pop('module')]
    if class_obj.__name__ in ('Google','Dork'):
        exit('This feature is no longer supported!')
    if class_obj.__name__ == 'Restart':
        main(class_obj(**var).go(**cache))
    class_obj(**var).go()
if __name__=="__main__":
    main(Args())
