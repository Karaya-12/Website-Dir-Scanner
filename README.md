# Website-Dir-Scanner
Website Directory Command Line Sannner (Based on Mauro Soria's dirsearch)

This is mainly my DLUT 2018 autumn semester network security project.

You should definitely check out Mauro Soria's original tool, link's down below.

https://github.com/maurosoria/dirsearch

Current Release: v1.10 (2018.12.25)

## Overview
Website Dir Scanner is a simple command line tool written in Python 3, which is designed to brute force directories and files in websites based on local dictionary.

## Supported Operating Systems
- Linux (Developed with Ubuntu 18.04)
- Windows XP/7/8/10 (Not Tested Yet)
- MacOSX (Not Tested Yet)

## Features
- Multithreaded (1 ~ 50)
- Keep connections alive
- Multiple extensions supported
- 3 different formats of scanning reports supported (Plain Text Report, JSON Report, Simple Report)
- Heuristically detect invalid web pages
- Recursive brute forcing supported
- HTTP proxy supported
- User agent customization
- Batch processing
- Request delaying & timeout

## Requirements
### Imported Packages
- chardet
- colorama
- requests
### Installation
```
$ cd ./sources
```
```
$ pip install -r requirements.txt
```

## Usage
Check out the built-in instruction
```
$ cd ./Website-Dir-Scanner
```
```
$ python DirScanner.py -h
```

## About Wordlists
Dictionary must be text files (_.txt).
Except for the lines with keyword '%EXT%' in them, every line will be read and processed by the scanner.
Those keywords '%EXT%' will be replaced with user custom extension(s) during the scanning process.

Example:
- example/
- example.%EXT%

If command line passed in user custom extensions - 'asp' and 'aspx'.
Scanner will replace the keyword '%EXT%' with given extensions and following dictionary will be generated:
- example/
- example.asp
- example.aspx

You can also use -f | --force-extensions switch to append extensions to every word in the wordlists (like DirBuster).

## License
MIT License

## Contributors
Note: You should definitely check out the link down below, which is the original tool --> 'dirsearch' developed by Mauro Soria (maurosoria).

https://github.com/maurosoria/dirsearch

Special thanks to these great developers of original tool (dirsearch).
- Mauro Soria
- Bo0oM
- liamosaur
- redshark1802
- SUHAR1K
- FireFart
- k2l8m11n2
- vlohacks
- r0p0s3c
