#   Copyright 2021, 2022 hidenorly
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
import csv
import itertools
import os
import json

from bs4 import BeautifulSoup
import tozanguchiDic
import mountainInfoDic

tozanguchiDic = tozanguchiDic.getTozanguchiDic()

class MountainDetailInfo:
  mountainInfoDic = mountainInfoDic.getMountainInfoDic()

  def getMountainDetailInfo(mountainName):
    result = None

    if( mountainName in MountainDetailInfo.mountainInfoDic):
      result = MountainDetailInfo.mountainInfoDic[mountainName]
    else:
      pos = mountainName.find("_")
      if pos != -1:
        mountainName = mountainName[0 : pos - 1 ]
      pos = mountainName.find("（")
      if pos != -1:
        mountainName = mountainName[0 : pos - 1 ]
      for aMountainName, anInfo in MountainDetailInfo.mountainInfoDic.items():
        if aMountainName.find( mountainName )!=-1:
          result = anInfo
          break

    return result


class StrUtil:
  @staticmethod
  def ljust_jp(value, length, pad = " "):
    count_length = 0
    for char in value.encode().decode('utf8'):
      if ord(char) <= 255:
        count_length += 1
      else:
        count_length += 2
    return value + pad * (length-count_length)


class TozanguchiCache:
  CACHE_BASE_DIR = os.path.expanduser("~")+"/.cache/tozanguchi"

  @staticmethod
  def ensureCacheStorage():
    if not os.path.exists(TozanguchiCache.CACHE_BASE_DIR):
      os.makedirs(TozanguchiCache.CACHE_BASE_DIR)

  @staticmethod
  def getCacheFilename(url):
    result = url
    pos = str(url).rfind("/")
    if pos!=-1:
      result = url[pos+1:len(url)]
    return result

  @staticmethod
  def getCachePath(url):
    return TozanguchiCache.CACHE_BASE_DIR+"/"+TozanguchiCache.getCacheFilename(url)

  @staticmethod
  def storeParkInfoAsCache(url, result):
    TozanguchiCache.ensureCacheStorage()
    cachePath = TozanguchiCache.getCachePath( url )

    with open(cachePath, 'w', encoding='UTF-8') as f:
      json.dump(result, f, indent = 4, ensure_ascii=False)
      f.close()

  @staticmethod
  def restoreParkInfoAsCache(cachePath):
    result = None
    with open(cachePath, 'r', encoding='UTF-8') as f:
      result = json.load(f)
    return result

  @staticmethod
  def getCachedParkInfo(url):
    result = None
    cachePath = TozanguchiCache.getCachePath( url )
    if os.path.exists( cachePath ):
      result = TozanguchiCache.restoreParkInfoAsCache( cachePath )

    return result

  @staticmethod
  def getRawParkInfo(url):
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

    return result

  @staticmethod
  def getParkInfo(url, forceReload = False):
    result = TozanguchiCache.getCachedParkInfo( url )
    if result == None or forceReload:
      result = TozanguchiCache.getRawParkInfo( url )
      TozanguchiCache.storeParkInfoAsCache( url, result )
    return result



class TozanguchiUtil:
  def getMountainKeys(key):
    result = []
    for dicKey, value in tozanguchiDic.items():
      if dicKey.startswith(key):
        result.append( dicKey )
    return result

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

  def getParkInfo(url, forceReload = False):
    result = TozanguchiCache.getParkInfo(url, forceReload)

    return TozanguchiUtil.maintainParkInfo(result)

  def showListAndDic(result, indent, startIndent):
    for key, value in parkInfo.items():
      if isinstance(value, list):
        print(" "*startIndent + StrUtil.ljust_jp(key, indent-startIndent) + " : ", end="")
        firstLine = True
        for aValue in value:
          if firstLine:
            print( str(aValue) )
            firstLine = False
          else:
            print(" "*(indent+3) + str(aValue) )
      else:
        print("    " + StrUtil.ljust_jp(key,indent-startIndent) + " : " + str(value))
    print("")

  def printMountainDetailInfo(mountainName):
    info = MountainDetailInfo.getMountainDetailInfo( mountainName )
    if info!=None:
      print( StrUtil.ljust_jp("  altitude", 20) + " : " + info["altitude"] )
      print( StrUtil.ljust_jp("  area", 20) + " : " + info["area"] )
      print( StrUtil.ljust_jp("  difficulty", 20) + " : " + info["difficulty"] )
      print( StrUtil.ljust_jp("  fitnessLevel", 20) + " : " + info["fitnessLevel"] )
      print( StrUtil.ljust_jp("  type", 20) + " : " + info["type"] )
      print( "" )


class MountainFilterUtil:
  @staticmethod
  def openCsv( fileName, delimiter="," ):
    result = []
    if os.path.exists( fileName ):
      file = open( fileName )
      if file:
        reader = csv.reader(file, quoting=csv.QUOTE_MINIMAL, delimiter=delimiter)
        for aRow in reader:
          data = []
          for aCol in aRow:
            aCol = aCol.strip()
            if aCol.startswith("\""):
              aCol = aCol[1:len(aCol)]
            if aCol.endswith("\""):
              aCol = aCol[0:len(aCol)-1]
            data.append( aCol )
          result.append( data )
    return result

  @staticmethod
  def isMatchedMountainRobust(arrayData, search):
    result = False
    for aData in arrayData:
      if aData.startswith(search) or search.startswith(aData):
        result = True
        break
    return result


  @staticmethod
  def mountainsIncludeExcludeFromFile( mountains, excludeFile, includeFile ):
    result = set()
    excludes = set( itertools.chain.from_iterable( MountainFilterUtil.openCsv( excludeFile ) ) )
    includes = set( itertools.chain.from_iterable( MountainFilterUtil.openCsv( includeFile ) ) )
    for aMountain in includes:
      mountains.add( aMountain )
    for aMountain in mountains:
      if not MountainFilterUtil.isMatchedMountainRobust( excludes, aMountain ):
        result.add( aMountain )
    return result


if __name__=="__main__":
  parser = argparse.ArgumentParser(description='Parse command line options.')
  parser.add_argument('args', nargs='*', help='mountain name such as 富士山')
  parser.add_argument('-c', '--compare', action='store_true', default=False, help='compare tozanguchi per climbtime')
  parser.add_argument('-r', '--renew', action='store_true', default=False, help='get latest data although cache exists')
  parser.add_argument('-e', '--exclude', action='store', default='', help='specify excluding mountain list file e.g. climbedMountains.lst')
  parser.add_argument('-i', '--include', action='store', default='', help='specify including mountain list file e.g. climbedMountains.lst')
  args = parser.parse_args()

  if len(args.args) == 0:
    parser.print_help()
    exit(-1)

  mountainKeys = set()
  mountains = set( args.args )
  mountains = MountainFilterUtil.mountainsIncludeExcludeFromFile( mountains, args.exclude, args.include )
  for aMountain in mountains:
    keys = TozanguchiUtil.getMountainKeys(aMountain)
    for aMountainKey in keys:
      mountainKeys.add( aMountainKey )

  for aMountain in mountainKeys:
    print(aMountain + ":")
    if not args.compare:
      TozanguchiUtil.printMountainDetailInfo( aMountain )
    tozanguchi = tozanguchiDic[aMountain]
    for aTozanguchi, theUrl in tozanguchi.items():
      parkInfo = TozanguchiUtil.getParkInfo(theUrl, args.renew)
      if not args.compare:
        # normal tozanguchi dump mode
        print( "  " + StrUtil.ljust_jp(aTozanguchi, 18) + " : " + theUrl )
        TozanguchiUtil.showListAndDic(parkInfo, 20, 4)
      else:
        # tozanguchi compare dump mode
        if "主要登山ルート" in parkInfo:
          climbTimes = parkInfo["主要登山ルート"]
          for aClimbTime in climbTimes:
            _theMountain = aMountain
            pos = _theMountain.find("_")
            if pos!=-1:
              _theMountain = _theMountain[0:pos-1]

            _mountains = _theMountain.split("・")
            for _aMountain in _mountains:
              pos = aClimbTime.find(_aMountain)
              if pos!=-1:
                print( "  " + StrUtil.ljust_jp(aTozanguchi, 18) + " : " + aClimbTime )
                break;
  

