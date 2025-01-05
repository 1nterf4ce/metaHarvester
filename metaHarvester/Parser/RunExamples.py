from Utils.Colors import console
import sys

Futures = """
Each module of this project supports working with different goals, file extensions, etc.
The task of this project is to massively scan a large number of sites and collect information about their infrastructure.

Opportunities:
1. Interruption/Resuming the session.
2. Support for proxy and Tor networks.
3. The ability to filter documents by extensions, size, creation date and number of downloaded documents.
4. Three report formats.(csv - (default), json and txt)
5. Multithreaded download with progress display
6. Additional search for email addresses and phone numbers in documents.
7. All modules use recursive file search.
8. It is possible to search and download interesting files (configuration files, etc.).
9.File search robots.txt and loading its contents into memory.
10.The most simple API and the ability to quickly and easily expand classes and add new features.
11. The ability to clear metadata from documents.
12. Using "Google dorks" to search for information about the goal.
13. The ability to use your own "Google dorks" to search for information about the goal.
14. The ability to import goals from files of 3 formats: csv, json, txt. For csv and json files, use the entry: file.csv[column_name]
"""

shared_args = f"""
{Futures}
Some arguments and thier description:
[-t,  --targets]     -t example.com "targets_file.csv['site']" targets.txt "target_json.txt['url']"
[-e,  --extensions]  -e pdf doc docx
[-s,  --size]        -s ">1MB...<2MB" - files in range from 1MB before 2MB  or ">1.5MB" files more 1.5 MB
[--all, --all-files] --all      if this argument is specified, it will download all files, regardless of the extension
[--i, --intresting-files]  --i  if this argument is specified, it will search for files with additional extensions
[-oC,-oJ,-oT]        -oC report.csv   Save report in csv file. oJ - json file, oT - txt file
[-d,  --date]        -d ">20230101-15:00:00" or ">2023-01-01...<2023-02-02"
[--dork]             --dork site:{"{domain}"}.  the value for the domain argument will be taken from the -t argument

Available modules:
google
dork
index-of
clear
extract
downloader
crawler
restart
passgen

Use {sys.argv[0]} -hh with module name.
[bold]{sys.argv[0]} -hh google[/bold] - for google module info
"""

def print_help_info(module:str):
    return f"""
    Examples:
{sys.argv[0]} {module} -t example.com                                  - simple usage
{sys.argv[0]} {module} -t example.com -s ">10KB...<1MB"                - with a filter by file sizes
{sys.argv[0]} {module} -t example.com -e pdf -s ">10KB...<1MB"         - with a filter by file extension(only pdf docs) and file sizes
{sys.argv[0]} {module} -t example.com -w 60 -c 10                      - with a filter by waiting 60 seconds and the number of files equal to 10
{sys.argv[0]} {module} -t example.com -oT report.txt                   - with a write result in txt file "report.txt"
{sys.argv[0]} {module} -t example.com --auto-remove                    - with a deleting files after downloading
{sys.argv[0]} {module} -t example.com --tor --i                        - with a using Tor network and find intresting files
{sys.argv[0]} {module} -t target.csv['site'] --tor --i -w 60 -c 10 -e docx --auto-remove -s ">10B...<1GB" -oJ report.json
"""
GoogleHelp = f"""
This module is designed to search for documents for the specified purposes in the Google search engine.
It uses the latest methods of searching and selecting documents.
{print_help_info('google')}
""" 

IndexOfHelp = f"""
Use this module to search for files in open directories. It can filter files by extension, creation date and size.
The arguments are like the Google module and one additional one is "date"  -d, --date
{print_help_info(module='index-of')}
{sys.argv[0]} -t example.com -d ">2023-01-01-15:00:00"
{sys.argv[0]} -t example.com -d ">2023-01-01-15:00:00...<2023-02-02"
{sys.argv[0]} -t example.com -d ">01012023"
Any date format is supported!"""


CrawlerHelp = f"""
Use this module to search for documents on the site.
It is also able to extract phone numbers, email addresses and text input fields from the page.
It recursively crawls the entire site, excluding links to other domains.

{print_help_info('crawler')}
"""

DorkHelp = f"""
Use this module to search for Google dorks.
You can specify your dork, which will search for information for the specified purposes from the -t argument, 
or use ready-made dorks prescribed in the module. You can also specify the number of pages viewed (3 by default).
This module uses the latest technology to search for a subdomain of the site, excluding domains already found with each request.Thus,
it makes scanning less noticeable and faster, in comparison with brute force, but less effective, because it does not find all domains

{sys.argv[0]} dork -t example.com -w 60 --tor
{sys.argv[0]} dork -t example.com --dork site:{"{domain}"}  domain from argument -t
"""

ExtractHelp = f"""
Use this module for extract metadata from local files or dirs with files

{sys.argv[0]} extract -t file.docx file.pdf pdf_directory 
{sys.argv[0]} extract -t file.docx file.pdf pdf_directory --auto-remove
{sys.argv[0]} extract -t file.docx file.pdf pdf_directory  -oT
"""

ClearHelp = F"""
Use this module for clear files or directory with files from metadata

{sys.argv[0]} clear -t file.jpg doc_files_catalog file.docx
"""


RestartHelp = f"""
Use this module for restart saved session

{sys.argv[0]} restart -t session-google-example.com.json
"""

DownloaderHelp = f"""
Use this module for downloading files from links. Suppoted any file format!

{sys.argv[0]} downloader -t https://example.com/file.jpg https://example.com/file2.jpg
"""

PassgenHelp = f"""
Use this module for generate passwords from founded usernames.
This module using unique methods for define username or person name for compilation passwords list.

{sys.argv[0]} passgen -t Users-example.com.txt Users2-example.com.txt 
"""