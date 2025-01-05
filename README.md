# METAHARVESTER 
***
**metaHarvester** - A program for automated document search and metadata extraction from them. 
Each module of this project supports working with different goals, file extensions, etc. 
The task of this project is to massively scan a large number of sites and collect information about their infrastructure. 
***
#### **Opportunities**:
-  ✅ 1. Interruption/Resuming the session.
-  ✅ 2. Support for proxy and Tor networks.
-  ✅ 3. The ability to filter documents by extensions.
-  ✅ 4. The ability to filter documents by size.
-  ✅ 5. The ability to filter documents by creation date. 
-  ✅ 6. The ability to filter documents by number of downloaded documents.
-  ✅ 7. Three report formats.(csv - (default), json and txt)
-  ✅ 8. Multithreaded download with progress display
-  ✅ 9. Additional search for email addresses and phone numbers in documents.
-  ✅ 10. All modules use recursive file search.
-  ✅ 11. It is possible to search and download interesting files (configuration files, etc.).
-  ✅ 12. Extracting metadata from local files.
-  ✅ 13. File search robots.txt and loading its contents into memory.
-  ✅ 14. The most simple API and the ability to quickly and easily expand classes and add new features.(Examples in metaHarvester.py file)
-  ✅ 15. The ability to clear metadata from documents or replace on random data.
- ❌ 16. Using "Google dorks" to search for information about the goal.(deprecated!)
- ❌ 17. The ability to use your own "Google dorks" to search for information about the goal.(deprecated)
-  ✅ 18. The ability to import goals from files of 3 formats: csv, json, txt. For csv and json files, use the entry: file.csv[column_name]
- ✅ 19. Generating a list of passwords from found names
-  ✅ 20. Searching for email addresses and phone numbers (available in the **crawler** module)
-  ✅ 21. The index-of module has been updated to automatically search for an open directory in Google if the site content does not match the patterns.
-  ✅ 22. Support for all open directory page templates
-  ✅ 23. For Google and Google Dork modules, a function has been added to bypass captcha via: public proxies, private proxies, or the Tor network
-  ✅ 24. Automatic addition of cookies to requests
-  ✅ 25. Support for formats: '.pdf', '.doc', '.docx', '.ppt', '.xlsx', '.xls', '.pptx', '.jpg', '.jpeg', '.bmp', '.png', '.tif' (More details in the Parser/ArgumentsParser.py file)
-  ✅ 26. Added the ability to download all files from the site, ignoring file extensions
-  ✅ 27. Search for input fields on pages (available in **crawler** module)
***
> #### **Available modules:**
> ❌ google  
> ❌ dork  
> ✅ index-of  
> ✅ clear  
> ✅ extract  
> ✅ downloader  
> ✅ crawler  
> ✅ restart  
> ✅ passgen  

***
#### **Install:**
python 3.10+ \
`pip install -r requirements.txt` \
`python3 metaHarvester.py -h` \
`python3 metaHarvester.py crawler -h`  

***
#### **Shared Arguments**
<table>
<tr><th>Arguments</th><th>Option</th><th>Description</th></tr>
<tr><td> -t,  --targets </td><td> -t  </td><td> example.com "targets_file.csv['site']" targets.txt "target_json.txt['url']" </td></tr>   
<tr><td> -e,  --extensions </td><td> -e </td><td> pdf doc docx</td></tr>   
<tr><td> -s,  --size </td><td> -s </td><td> ">1MB...<2MB" - files in range from 1MB before 2MB  or ">1.5MB" files more 1.5 MB</td></tr>   
<tr><td> --all, --all-files </td><td> --all </td><td> if this argument is specified, it will download all files, regardless of the extension</td></tr>   
<tr><td> --i, --intresting-files </td><td> --i </td><td> if this argument is specified, it will search for files with additional extensions</td></tr>   
<tr><td> -oC,-oJ,-oT </td><td> -oC report.csv </td><td> Save report in csv file. oJ - json file, oT - txt file</td></tr>   
<tr><td> -d,  --date </td><td> -d ">20230101-15:00:00"  </td><td>  ">2023-01-01...<2023-02-02"</td></tr>   
<tr><td> --dork </td><td> --dork site:{"{domain}"}. </td><td> the value for the domain argument will be taken from the -t argument</td></tr>   
</table>


***
> #### **Run Examples:**
> `python3 metaHarvester.py  -t example.com                                  - simple usage`  
> `python3 metaHarvester.py  -t example.com -s ">10KB...<1MB"                - with a filter by file sizes`  
> `python3 metaHarvester.py  -t example.com -e pdf -s ">10KB...<1MB"         - with a filter by file extension(only pdf docs) and file sizes`  
> `python3 metaHarvester.py  -t example.com -w 60 -c 10                      - with a filter by waiting 60 seconds and the number of files equal to 10`  
> `python3 metaHarvester.py  -t example.com -oT report.txt                   - with a write result in txt file "report.txt"`  
> `python3 metaHarvester.py  -t example.com --auto-remove                    - with a deleting files after downloading>`  
> `python3 metaHarvester.py  -t example.com --tor --i                        - with a using Tor network and find intresting files`  
> `python3 metaHarvester.py  -t target.csv['site'] --tor --i -w 60 -c 10 -e docx --auto-remove -s ">10B...<1GB" -oJ report.json`  
> Using option: `--help-all` for show all reference
***
⚠️ metaHarvester is for educational/research purposes only. The author does NOT take ANY responsibility and/or liability for how you choose to use any tools/source code/any files provided. The author and anyone associated with the author will not be held liable for any losses and/or damages in connection with the use of ANY files provided by metaHarvester.
