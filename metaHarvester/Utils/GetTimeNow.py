from datetime import datetime

def today(filename=False) -> str:
    if filename:
        return datetime.strftime(datetime.now(),'%d%m%y-%H%M%S')
    return datetime.strftime(datetime.now(),'%d.%m.%y-%H:%M:%S')