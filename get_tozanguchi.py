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
import datetime
import re

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

  @staticmethod
  def toInt(value):
    nums = re.findall(r"\d+", value) #re.sub(r"\D", "", value)
    result = 0
    if len(nums) > 0:
      result = int( nums[0] )
    return result


class TozanguchiCache:
  CACHE_BASE_DIR = os.path.expanduser("~")+"/.cache/tozanguchi"
  CACHE_EXPIRE_HOURS = 24*365 # approx. 1 year

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
    dt_now = datetime.datetime.now()
    result["lastUpdate"] = dt_now.strftime("%Y-%m-%d %H:%M:%S")

    with open(cachePath, 'w', encoding='UTF-8') as f:
      json.dump(result, f, indent = 4, ensure_ascii=False)
      f.close()

    del result["lastUpdate"]

  @staticmethod
  def isValidCache( lastUpdateString ):
    result = False
    lastUpdate = datetime.datetime.strptime(lastUpdateString, "%Y-%m-%d %H:%M:%S")
    dt_now = datetime.datetime.now()
    if dt_now < ( lastUpdate+datetime.timedelta(hours=TozanguchiCache.CACHE_EXPIRE_HOURS) ):
      result = True

    return result

  @staticmethod
  def restoreParkInfoAsCache(cachePath):
    result = None
    with open(cachePath, 'r', encoding='UTF-8') as f:
      _result = json.load(f)

    if "lastUpdate" in _result:
      if TozanguchiCache.isValidCache( _result["lastUpdate"] ):
        del _result["lastUpdate"]
        result = _result

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
  def getParkInfo(url, forceReload = False, noneIfCacheMiss = False):
    result = TozanguchiCache.getCachedParkInfo( url )
    if (result == None or forceReload) and (noneIfCacheMiss == False):
      result = TozanguchiCache.getRawParkInfo( url )
      TozanguchiCache.storeParkInfoAsCache( url, result )
    return result



class TozanguchiUtil:
  @staticmethod
  def getMountainKeys(key):
    result = []
    for dicKey, value in tozanguchiDic.items():
      if dicKey.startswith(key):
        result.append( dicKey )
    return result

  @staticmethod
  def maintainParkInfo(result):
    if result!=None and "主要登山ルート" in result:
      routes = result["主要登山ルート"].split("）")
      newRoutes = []
      for aRoute in routes:
        aRoute = aRoute.strip()
        if aRoute:
          newRoutes.append( aRoute+")" )
      result["主要登山ルート"] = newRoutes
    return result

  @staticmethod
  def getParkInfo(url, forceReload = False, noneIfCacheMiss = False):
    result = TozanguchiCache.getParkInfo(url, forceReload, noneIfCacheMiss)

    return TozanguchiUtil.maintainParkInfo(result)

  @staticmethod
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

  @staticmethod
  def printMountainDetailInfo(mountainName):
    info = MountainDetailInfo.getMountainDetailInfo( mountainName )
    if info!=None:
      print( StrUtil.ljust_jp("  altitude", 20) + " : " + info["altitude"] )
      print( StrUtil.ljust_jp("  area", 20) + " : " + info["area"] )
      print( StrUtil.ljust_jp("  difficulty", 20) + " : " + info["difficulty"] )
      print( StrUtil.ljust_jp("  fitnessLevel", 20) + " : " + info["fitnessLevel"] )
      print( StrUtil.ljust_jp("  type", 20) + " : " + info["type"] )
      print( "" )


  @staticmethod
  def getClimbTimeMinutes(mountainName, parkInfo):
    result = 0

    pos = mountainName.find("_")
    if pos!=-1:
      mountainName = mountainName[0:pos-1]
    _mountains = mountainName.split("・")

    if "主要登山ルート" in parkInfo:
      climbTimes = parkInfo["主要登山ルート"]
      for aClimbTime in climbTimes:
        for _aMountain in _mountains:
          pos = aClimbTime.find(_aMountain)
          if pos!=-1:
            pos = aClimbTime.find("往復所要時間：")
            if pos!=-1:
              pos2 = aClimbTime.find("分)", pos)
              if pos2!=-1:
                result = aClimbTime[pos+7:pos2]
                pos = result.find("時間")
                if pos!=-1:
                  result = int(result[0:pos])*60+int(result[pos+2:len(result)])
                else:
                  result = int(result)
            break;

    return result

  @staticmethod
  def getMinutesFromHHMM(timeHHMM):
    result = 0

    if timeHHMM!="":
      pos = str(timeHHMM).find(":")
      if pos!=-1:
        result = int( timeHHMM[0:pos] ) * 60 + int( timeHHMM[pos+1:len(timeHHMM)] )
      else:
        result = int( timeHHMM )

    return result

  @staticmethod
  def getTheNumberOfCarPark(parkInfo):
    result = 0
    if "駐車台数" in parkInfo:
      parks = parkInfo["駐車台数"]
      pos = parks.find("台")
      if pos!=-1:
        parks = parks[0:pos]
      result = StrUtil.toInt( parks ) #int( parks )

    return result

  @staticmethod
  def isAcceptableTozanguchi(mountainName, parkInfo, minClimbTimeMinutes, maxClimbTimeMinutes, minPark):
    result = True

    climbTimeMinutes = TozanguchiUtil.getClimbTimeMinutes(mountainName, parkInfo)
    if ( maxClimbTimeMinutes and climbTimeMinutes > maxClimbTimeMinutes ) or ( minClimbTimeMinutes and climbTimeMinutes < minClimbTimeMinutes ) or TozanguchiUtil.getTheNumberOfCarPark(parkInfo) < int(minPark):
      result = False

    return result

  @staticmethod
  def showParkAndRoute(mountainName, parkInfo):
    _mountains = re.split(r'[・/_]', mountainName)
    mountains=set()
    for _aMountain in _mountains:
      _aMountain = _aMountain.strip()
      mountains.add(_aMountain)

    theNumOfCarInPark = ""
    if "駐車台数" in parkInfo:
      theNumOfCarInPark = " ("+parkInfo["駐車台数"]+")"
    if "主要登山ルート" in parkInfo:
      climbTimes = parkInfo["主要登山ルート"]
      for aClimbTime in climbTimes:
        for _aMountain in mountains:
          pos = aClimbTime.find(_aMountain)
          if pos!=-1:
            print( "  " + StrUtil.ljust_jp(aTozanguchi, 18) + " : " + aClimbTime + theNumOfCarInPark )
            break;

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
  def getSetOfCsvs( csvFiles ):
    result = set()
    csvFiles = str(csvFiles).split(",")
    for aCsvFile in csvFiles:
      aCsvFile = os.path.expanduser( aCsvFile )
      theSet = set( itertools.chain.from_iterable( MountainFilterUtil.openCsv( aCsvFile ) ) )
      result = result.union( theSet )
    return result

  @staticmethod
  def mountainsIncludeExcludeFromFile( mountains, excludeFile, includeFile ):
    result = set()
    includes = set()
    excludes = set()
    for anExclude in excludeFile:
      excludes =  excludes | MountainFilterUtil.getSetOfCsvs( anExclude )
    for anInclude in includeFile:
      includes = includes | MountainFilterUtil.getSetOfCsvs( anInclude )
    for aMountain in includes:
      mountains.add( aMountain )
    for aMountain in mountains:
      if not MountainFilterUtil.isMatchedMountainRobust( excludes, aMountain ):
        result.add( aMountain )
    return result

  @staticmethod
  def mountainsHashExcludeFromFile( mountains, excludeFile ):
    result = {}
    excludes = MountainFilterUtil.getSetOfCsvs( excludeFile )
    for aMountainName, theMountainInfo in mountains:
      if not MountainFilterUtil.isMatchedMountainRobust( excludes, aMountainName ):
        result[ aMountainName ] = theMountainInfo
    return result


if __name__=="__main__":
  parser = argparse.ArgumentParser(description='Parse command line options.')
  parser.add_argument('args', nargs='*', help='mountain name such as 富士山')
  parser.add_argument('-c', '--compare', action='store_true', default=False, help='compare tozanguchi per climbtime')
  parser.add_argument('-r', '--renew', action='store_true', default=False, help='get latest data although cache exists')
  parser.add_argument('-t', '--maxTime', action='store', default='', help='specify max climb time e.g. 5:00')
  parser.add_argument('-b', '--minTime', action='store', default='', help='specify min climb time e.g. 4:30')
  parser.add_argument('-e', '--exclude', action='append', default=[], help='specify excluding mountain list file e.g. climbedMountains.lst')
  parser.add_argument('-i', '--include', action='append', default=[], help='specify including mountain list file e.g. climbedMountains.lst')
  parser.add_argument('-nn', '--mountainNameOnly', action='store_true', default=False, help='specify if you want to output mountain name only')
  parser.add_argument('-on', '--outputNotFound', action='store_true', default=False, help='specify if you want to output not found mountain too. For -nn')
  parser.add_argument('-s', '--sortReverse', action='store_true', default=False, help='specify if you want to output as reverse sort order')
  parser.add_argument('-p', '--minPark', action='store', default=0, help='specify the number of minimum car parking e.g. 0')
  parser.add_argument('-l', '--listAllCache', action='store_true', default=False, help='specify if you want to list up cached park')
  parser.add_argument('-nd', '--noDetails', action='store_true', default=False, help='specify if you want to disable to output the mountain info.')

  args = parser.parse_args()

  mountainKeys = set()
  mountains = set()
  if args.listAllCache:
    mountains = set( tozanguchiDic.keys() )
  else:
    mountains = set( args.args )
  mountains = MountainFilterUtil.mountainsIncludeExcludeFromFile( mountains, args.exclude, args.include )

  if len(mountains) == 0 and not args.listAllCache:
    parser.print_help()
    exit(-1)

  for aMountain in mountains:
    keys = TozanguchiUtil.getMountainKeys(aMountain)
    for aMountainKey in keys:
      mountainKeys.add( aMountainKey )

  minClimbTimeMinutes = TozanguchiUtil.getMinutesFromHHMM(args.minTime)
  maxClimbTimeMinutes = TozanguchiUtil.getMinutesFromHHMM(args.maxTime)

  excludes = MountainFilterUtil.getSetOfCsvs( args.exclude )
  mountainNames = set()
  urlMap = {}
  for aMountain in mountainKeys:
    if not MountainFilterUtil.isMatchedMountainRobust( excludes, aMountain ):
      tozanguchi = tozanguchiDic[aMountain]
      result = {}
      for aTozanguchi, theUrl in tozanguchi.items():
        parkInfo = TozanguchiUtil.getParkInfo(theUrl, args.renew, args.listAllCache)
        if parkInfo != None and TozanguchiUtil.isAcceptableTozanguchi( aMountain, parkInfo, minClimbTimeMinutes, maxClimbTimeMinutes, args.minPark ):
          result [ aTozanguchi ] = parkInfo
          urlMap[ str(parkInfo) ] = theUrl

      if not args.mountainNameOnly and len(result)!=0:
        print(aMountain + ":")
        if not args.compare and not args.noDetails:
          TozanguchiUtil.printMountainDetailInfo( aMountain )

      result = dict( sorted( result.items(), reverse=args.sortReverse, key=lambda _data: ( TozanguchiUtil.getClimbTimeMinutes(aMountain, _data[0]), TozanguchiUtil.getClimbTimeMinutes(aMountain, _data[1]) ) ) )

      for aTozanguchi, parkInfo in result.items():
        mountainNames = mountainNames.union( set( aMountain.split("・") ) )
        if not args.mountainNameOnly:
          if not args.compare:
            # normal tozanguchi dump mode
            print( "  " + StrUtil.ljust_jp(aTozanguchi, 18) + " : " + urlMap[ str(parkInfo) ] )
            TozanguchiUtil.showListAndDic(parkInfo, 20, 4)
          else:
            # tozanguchi compare dump mode
            TozanguchiUtil.showParkAndRoute( aMountain, parkInfo )

  if args.mountainNameOnly:
    mountains = mountainNames
    if args.outputNotFound:
      mountains = mountains.union( set( set(args.args) - mountainKeys) )
    for aMountain in mountains:
      if not MountainFilterUtil.isMatchedMountainRobust( excludes, aMountain ):
        print( aMountain + " ", end="" )
    print( "" )
