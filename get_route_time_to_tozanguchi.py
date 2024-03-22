#   Copyright 2021, 2022, 2023, 2024 hidenorly
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
import re
import os
from datetime import timedelta, datetime
import json
import glob

from get_tozanguchi import MountainDetailInfo
from get_tozanguchi import StrUtil
from get_tozanguchi import TozanguchiCache
from get_tozanguchi import TozanguchiUtil
from get_tozanguchi import MountainFilterUtil

import tozanguchiDic
import mountainInfoDic

from get_route_time import WebUtil
from get_route_time import RouteUtil



tozanguchiDic = tozanguchiDic.getTozanguchiDic()


class GeoUtil:
  @staticmethod
  def getLatitudeLongitude(latitude_longitude):
    latitude = None
    longitude = None
    pattern = r'(\d+\.\d+)\s+(\d+\.\d+)'
    match = re.search(pattern, str(latitude_longitude))
    if match:
      latitude = match.group(1)
      longitude = match.group(2)
    return latitude, longitude


class GeoCache:
  DEFAULT_CACHE_BASE_DIR = os.path.expanduser("~")+"/.cache"
  DEFAULT_CACHE_ID = "geocache"
  CACHE_INFINITE = -1
  DEFAULT_CACHE_EXPIRE_HOURS = 24*30 # 30days

  def __init__(self, cacheId = None, expireHour = None, numOfCache = None):
    self.cacheBaseDir = os.path.join(GeoCache.DEFAULT_CACHE_BASE_DIR, cacheId) if cacheId else JsonCache.DEFAULT_CACHE_ID
    self.expireHour = expireHour if expireHour else JsonCache.DEFAULT_CACHE_EXPIRE_HOURS
    self.numOfCache = numOfCache if numOfCache else JsonCache.CACHE_INFINITE

  def ensureCacheStorage(self):
    if not os.path.exists(self.cacheBaseDir):
      os.makedirs(self.cacheBaseDir)

  def getCacheFilename(self, from_latitude, from_longitude, to_latitude, to_longitude, tag=None):
    result = f'{from_latitude}_{from_longitude}_{to_latitude}_{to_longitude}'
    if tag:
      result = f'{result}_{tag}.json'
    else:
      result = f'{result}.json'
    return result

  def getCachePath(self, from_latitude, from_longitude, to_latitude, to_longitude, tag=None):
    return os.path.join(self.cacheBaseDir, self.getCacheFilename(from_latitude, from_longitude, to_latitude, to_longitude, tag))

  def limitNumOfCacheFiles(self):
    if self.numOfCache!=self.CACHE_INFINITE:
      files = glob.glob(f'{self.cacheBaseDir}/*.json')
      files = sorted(files, key=os.path.getmtime, reverse=True)
      remove_files = files[self.numOfCache:]
      for aRemoveFile in remove_files:
        try:
          os.remove(aRemoveFile)
        except:
          pass


  def storeToCache(self, from_latitude, from_longitude, to_latitude, to_longitude, result, tag=None):
    self.ensureCacheStorage()
    cachePath = self.getCachePath( from_latitude, from_longitude, to_latitude, to_longitude, tag )
    dt_now = datetime.now()
    _result = {
      "lastUpdate":dt_now.strftime("%Y-%m-%d %H:%M:%S"),
      "data": result
    }
    with open(cachePath, 'w', encoding='UTF-8') as f:
      json.dump(_result, f, indent = 4, ensure_ascii=False)
      f.close()
    self.limitNumOfCacheFiles()


  def isValidCache(self, lastUpdateString):
    result = False
    lastUpdate = datetime.strptime(lastUpdateString, "%Y-%m-%d %H:%M:%S")
    dt_now = datetime.now()
    if self.expireHour == self.CACHE_INFINITE or ( dt_now < ( lastUpdate+timedelta(hours=self.expireHour) ) ):
      result = True

    return result

  def restoreFromCache(self, from_latitude, from_longitude, to_latitude, to_longitude, tag=None):
    result = None
    cachePath = self.getCachePath( from_latitude, from_longitude, to_latitude, to_longitude, tag )
    if os.path.exists( cachePath ):
      with open(cachePath, 'r', encoding='UTF-8') as f:
        _result = json.load(f)
        f.close()

      if "lastUpdate" in _result:
        if self.isValidCache( _result["lastUpdate"] ):
          result = _result["data"]

    return result

  @staticmethod
  def clearAllCache(cacheId):
    files = glob.glob(f'{os.path.join(JsonCache.DEFAULT_CACHE_BASE_DIR, cacheId)}/*.json')
    for aRemoveFile in files:
      try:
        os.remove(aRemoveFile)
      except:
        pass


class CachedRouteUtil:
  def __init__(self, cacheId = None, expireHour = None, numOfCache = None):
    self.cacheId = cacheId if cacheId else JsonCache.DEFAULT_CACHE_ID
    self.expireHour = expireHour if expireHour else JsonCache.DEFAULT_CACHE_EXPIRE_HOURS
    self.numOfCache = numOfCache if numOfCache else JsonCache.CACHE_INFINITE

    self.cache = GeoCache(self.cacheId, self.expireHour, self.numOfCache)

    self.driver = None

  def get_timezone_tag(self):
    result = None
    dt_now = datetime.now()

    hour = int(dt_now.hour)
    if dt_now.minute!=0:
      hour = hour + float(dt_now.minute/60)

    if 3 <= hour <= 5:
        result = "early_morning"
    elif 5 <= hour <= 8:
        result = "morning"
    elif 8 <= hour <= 10:
        result = "late_morning"
    elif 10 <= hour <= 13:
        result = "lunch"
    elif 13 <= hour <= 15:
        result = "late_lunch"
    elif 15 <= hour <= 18:
        result = "afternoon"
    elif 18 <= hour <= 20:
        result = "evening"
    elif 20 <= hour <= 22:
        result = "night"
    elif 22 <= hour <= 23 or 0 <= hour <= 3:
        result = "midnight"

    if dt_now.weekday()>=5:
      result = f'weekday_{result}'

    return result

  def get_directions_duration_minutes(self, lat1, lon1, lat2, lon2):
    duration_minutes = None
    directions_link = None
    tag = self.get_timezone_tag()
    cacheData = self.cache.restoreFromCache(lat1, lon1, lat2, lon2, tag)

    if cacheData:
      duration_minutes = cacheData["duration_minutes"]
      directions_link = cacheData["directions_link"]
    else:
      if not self.driver:
        self.driver = WebUtil.get_web_driver()

      duration_minutes, directions_link = RouteUtil.get_directions_duration_minutes(self.driver, lat1, lon1, lat2, lon2)
      _data = {
        "duration_minutes": duration_minutes,
        "directions_link": directions_link,
      }
      self.cache.storeToCache(latitude, longitude, aGeo[0], aGeo[1], _data, tag)

    return duration_minutes, directions_link




if __name__=="__main__":
  parser = argparse.ArgumentParser(description='Parse command line options.')
  parser.add_argument('args', nargs='*', help='mountain name such as 富士山')
  parser.add_argument('-f', '--longitudelatitude', action='store', default='35.658581 139.745433', help="Specify source place's longitutude latitude")
  parser.add_argument('-r', '--renew', action='store_true', default=False, help='get latest data although cache exists')
  parser.add_argument('-t', '--maxTime', action='store', default='', help='specify max route time e.g. 5:00')
  parser.add_argument('-b', '--minTime', action='store', default='', help='specify min route time e.g. 4:30')
  parser.add_argument('-e', '--exclude', action='append', default=[], help='specify excluding mountain list file e.g. climbedMountains.lst')
  parser.add_argument('-i', '--include', action='append', default=[], help='specify including mountain list file e.g. climbedMountains.lst')
  parser.add_argument('-nn', '--mountainNameOnly', action='store_true', default=False, help='specify if you want to output mountain name only')
  parser.add_argument('-nd', '--noDetail', action='store_true', default=False, help='specify if you want to show as simple mode')

  args = parser.parse_args()

  mountains = set( args.args )
  mountains = MountainFilterUtil.mountainsIncludeExcludeFromFile( mountains, args.exclude, args.include )
  latitude, longitude = GeoUtil.getLatitudeLongitude(args.longitudelatitude)

  minRouteTimeMinutes = TozanguchiUtil.getMinutesFromHHMM(args.minTime)
  maxRouteTimeMinutes = TozanguchiUtil.getMinutesFromHHMM(args.maxTime)

  cachedRouteUtil = CachedRouteUtil("routeTime", GeoCache.DEFAULT_CACHE_EXPIRE_HOURS, 1000)

  if len(mountains) == 0 or not latitude or not longitude:
    parser.print_help()
    exit(-1)

  # enumerate tozanguchi park geolocations per mountain
  tozanguchiParkInfos = {}
  detailParkInfo = {}
  for aMountain in mountains:
    if aMountain in tozanguchiDic:
      tozanguchis = tozanguchiDic[aMountain]
      tozanguchiParkInfos[ aMountain ] = set()
      for aTozanguchi, theUrl in tozanguchis.items():
        parkInfo = TozanguchiUtil.getParkInfo(theUrl)
        if parkInfo != None:
            if "緯度経度" in parkInfo:
              _latitude, _longitude = GeoUtil.getLatitudeLongitude(parkInfo["緯度経度"])
              tozanguchiParkInfos[ aMountain ].add( (_latitude, _longitude) )
              _parkInfo = {}
              _parkInfo["登山口"] = aTozanguchi
              _parkInfo.update(parkInfo)
              detailParkInfo[f'{_latitude}_{_longitude}'] = _parkInfo

  # enumerate route time to the tozanguchi park per mountain
  conditionedMountains = set()
  for aMountainName, tozanguchiParkGeos in tozanguchiParkInfos.items():
    for aGeo in tozanguchiParkGeos:
      duration_minutes, directions_link = cachedRouteUtil.get_directions_duration_minutes(latitude, longitude, aGeo[0], aGeo[1])
      if (maxRouteTimeMinutes==0 or duration_minutes>=minRouteTimeMinutes) and (maxRouteTimeMinutes==0 or duration_minutes<=maxRouteTimeMinutes):
        conditionedMountains.add(aMountainName)
        if not args.mountainNameOnly:
          if args.noDetail:
            print(f'{aMountainName} {aGeo[0]} {aGeo[1]} {duration_minutes} {directions_link}')
          else:
            print(aMountainName)
            detailParkInfo[f'{aGeo[0]}_{aGeo[1]}']["登山口への移動時間"] = '{:d}分 ({:02d}:{:02d})'.format(duration_minutes, int(duration_minutes/60), duration_minutes % 60)
            TozanguchiUtil.showListAndDic(detailParkInfo[f'{aGeo[0]}_{aGeo[1]}'], 22, 4)

  if args.mountainNameOnly:
    conditionedMountains = sorted(conditionedMountains)
    print( " ".join(conditionedMountains) )
