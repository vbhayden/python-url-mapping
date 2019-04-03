# python-url-mapping
Maps URL dependency chains and finds missing pages.  This is a barebones Python 3 script.

# Installation
There isn't much to install as this is a single Python 3 script.  If you need python, [Follow these instructions](http://docs.python-guide.org/en/latest/starting/install3/win/).

This script does use two libraries: BeautifulSoup and Requests.  If you are comfortable using pip, you can use:
```
pip install bs4
pip install requests
```

If not, there are manual instructions here:
1. [Install BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
1. [Install Requests](http://docs.python-requests.org/en/master/user/install/)

# How to Use
You can use this as a traditional command-line function via:

```
python.exe mapurls.py http://adlnet.gov --save
```

Alternatively, you can use this without the command line with the `mapurls` function:
```
results = mapurls("http://adlnet.gov", save=False, verbose=False)
```
