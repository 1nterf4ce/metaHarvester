from rich.console import Console
from rich.style import Style

custom_style = Style(color="#ff1100", bgcolor="black", bold=True)
#colors
info_color      = "#99ff99"
debug_color     = "#ffa500"
warning_color   = '#ffff66'
critical_color  = "#ff3300"
log_info_color  = 'cyan'

console = Console()
log_info = lambda x:console.print(f'[{log_info_color}][+] {x}[/{log_info_color}]')
info = lambda x:console.print(f'[{info_color}][+] {x}[/{info_color}]')
debug = lambda x:console.print(f'[{debug_color}][*] {x}[/{debug_color}]')
warning = lambda x:console.print(f'[{warning_color}][-] {x}[/{warning_color}]')
critical = lambda x:console.print(f'[{critical_color}][!] {x}[/{critical_color}]')


