#   Copyright 2021 hidenorly
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import sys
import requests
import argparse
import unicodedata
from bs4 import BeautifulSoup
import tozanguchiDic

tozanguchiDic = tozanguchiDic.getTozanguchiDic()

def getMountainKeys(key):
  result = []
  for dicKey, value in tozanguchiDic.items():
    if dicKey.startswith(key):
      result.append( dicKey )
  return result

def ljust_jp(value, length, pad = " "):
  count_length = 0
  for char in value.encode().decode('utf8'):
    if ord(char) <= 255:
      count_length += 1
    else:
      count_length += 2
  return value + pad * (length-count_length)

if __name__=="__main__":
  parser = argparse.ArgumentParser(description='Parse command line options.')
  parser.add_argument('args', nargs='*', help='mountain name such as 富士山')
  parser.add_argument('-c', '--compare', action='store_true', help='compare mountains per day')
  args = parser.parse_args()

  if len(args.args) == 0:
    parser.print_help()
    exit(-1)

  mountainKeys = []
  mountains = args.args
  for aMountain in mountains:
    keys = getMountainKeys(aMountain)
    for aMountainKey in keys:
      mountainKeys.append( aMountainKey )

  for aMountain in mountainKeys:
    print(aMountain + ":")
    tozanguchi = tozanguchiDic[aMountain]
    for aTozanguchi, theUrl in tozanguchi.items():
      print( "  " + ljust_jp(aTozanguchi, 18) + " : " + theUrl )
