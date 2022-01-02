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
import mountainInfoDic

tozanguchiDic = tozanguchiDic.getTozanguchiDic()
mountainInfoDic = mountainInfoDic.getMountainInfoDic()

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

def maintainParkInfo(result):
  if "主要登山ルート" in result:
    routes = result["主要登山ルート"].split("）")
    newRoutes = []
    for aRoute in routes:
      aRoute = aRoute.strip()
      if aRoute:
        newRoutes.append( aRoute+")" )
    result["主要登山ルート"] = newRoutes
  return result

def getParkInfo(url):
  result = {}
  res = requests.get(url)
  soup = BeautifulSoup(res.text, 'html.parser')
  if None != soup:
    dts = soup.find_all("dt")
    dds = soup.find_all("dd")
    # i should be starting from 0 and shoud use dts[i], dds[i] and should not require to split
    i = 1
    while( i<len(dts) and i<len(dds) ):
      key = dts[i*2-1].text.strip().split("\n")[0].strip()
      value = dds[i].text.strip().split("\n")[0].strip()
      result[key] = value
      i=i+1

  return maintainParkInfo(result)

def showListAndDic(result, indent, startIndent):
  for key, value in parkInfo.items():
    if isinstance(value, list):
      print(" "*startIndent + ljust_jp(key, indent-startIndent) + " : ", end="")
      firstLine = True
      for aValue in value:
        if firstLine:
          print( str(aValue) )
          firstLine = False
        else:
          print(" "*(indent+3) + str(aValue) )
    else:
      print("    " + ljust_jp(key,indent-startIndent) + " : " + str(value))
  print("")


def getMountainDetailInfo(mountainName):
  result = None

  if( mountainName in mountainInfoDic):
    result = mountainInfoDic[mountainName]
  else:
    pos = mountainName.find("_")
    if pos != -1:
      mountainName = mountainName[0 : pos - 1 ]
    pos = mountainName.find("（")
    if pos != -1:
      mountainName = mountainName[0 : pos - 1 ]
    for aMountainName, anInfo in mountainInfoDic.items():
      if aMountainName.find( mountainName )!=-1:
        result = anInfo
        break

  return result


def printMountainDetailInfo(mountainName):
  info = getMountainDetailInfo( mountainName )
  if info!=None:
    print( ljust_jp("  altitude", 20) + " : " + info["altitude"] )
    print( ljust_jp("  area", 20) + " : " + info["area"] )
    print( ljust_jp("  difficulty", 20) + " : " + info["difficulty"] )
    print( ljust_jp("  fitnessLevel", 20) + " : " + info["fitnessLevel"] )
    print( ljust_jp("  type", 20) + " : " + info["type"] )
    print( "" )


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
    printMountainDetailInfo( aMountain )
    tozanguchi = tozanguchiDic[aMountain]
    for aTozanguchi, theUrl in tozanguchi.items():
      print( "  " + ljust_jp(aTozanguchi, 18) + " : " + theUrl )
      parkInfo = getParkInfo(theUrl)
      showListAndDic(parkInfo, 20, 4)
