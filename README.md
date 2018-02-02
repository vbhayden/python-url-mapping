# python-url-mapping
Maps URL dependency chains and finds missing pages.  This is a barebones Python 3 script.

# Installation
There's nothing to install as this is a single Python 3 script.  If you need python, [Follow these instructions](http://docs.python-guide.org/en/latest/starting/install3/win/).

# How to Use
You can use this as a traditional command-line function via:

```
python.exe mapurls.py http://adlnet.gov --save
```

Alternatively, you can use this without the command line with the `mapurls` function:
```
results = mapurls("http://adlnet.gov", save=False, verbose=False)
```
