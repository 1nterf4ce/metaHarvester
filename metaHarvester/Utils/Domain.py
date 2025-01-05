def GetDomain(domain:str)->str:
    try:
        return domain.split('://')[1].split('/')[0]
    except IndexError:
        return domain.split('/')[0]