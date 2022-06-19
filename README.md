# tozanguchi

DO NOT USE THIS.

# Create tozanguchiDic.py

```
$ python3 tozanguchi_list_mountains.py "https://tozanguchinavi.com/mt" "https://tozanguchinavi.com/mt/page/" 2 2 > tozanguchiDic.py
```

# help

```
usage: get_tozanguchi.py [-h] [-c] [-r] [-t MAXTIME] [-e EXCLUDE] [-i INCLUDE] [-nn] [-on] [-s] [args ...]

Parse command line options.

positional arguments:
  args                  mountain name such as 富士山

optional arguments:
  -h, --help            show this help message and exit
  -c, --compare         compare tozanguchi per climbtime
  -r, --renew           get latest data although cache exists
  -t MAXTIME, --maxTime MAXTIME
                        specify max climb time e.g. 5:00
  -e EXCLUDE, --exclude EXCLUDE
                        specify excluding mountain list file e.g. climbedMountains.lst
  -i INCLUDE, --include INCLUDE
                        specify including mountain list file e.g. climbedMountains.lst
  -nn, --mountainNameOnly
                        specify if you want to output mountain name only
  -on, --outputNotFound
                        specify if you want to output not found mountain too. For -nn
  -s, --sortReverse     specify if you want to output as reverse sort order
```

# show tozanguchi detail

```
$ python3 get_tozanguchi.py 男体山
```

# show tozanguchi comparison

```
$ python3 get_tozanguchi.py 男体山 -c
```

# show tozanguchi comparison as larger climb time to smaller time

```
$ python3 get_tozanguchi.py 男体山 -c -s
```

# list tozanguchi under specified climb time

```
$ python3 get_tozanguchi.py 富士山 -c --maxTime=10:00
```
