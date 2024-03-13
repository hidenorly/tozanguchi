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

  args = parser.parse_args()

  mountains = set( args.args )
  mountains = MountainFilterUtil.mountainsIncludeExcludeFromFile( mountains, args.exclude, args.include )
  latitude, longitude = GeoUtil.getLatitudeLongitude(args.longitudelatitude)

  minRouteTimeMinutes = TozanguchiUtil.getMinutesFromHHMM(args.minTime)
  maxRouteTimeMinutes = TozanguchiUtil.getMinutesFromHHMM(args.maxTime)

  if len(mountains) == 0 or not latitude or not longitude:
    parser.print_help()
    exit(-1)

  # enumerate tozanguchi park geolocations per mountain
  tozanguchiParkInfos = {}
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

  # enumerate route time to the tozanguchi park per mountain
  driver = WebUtil.get_web_driver()
  conditionedMountains = set()
  for aMountainName, tozanguchiParkGeos in tozanguchiParkInfos.items():
    for aGeo in tozanguchiParkGeos:
      #directions_link = RouteUtil.generate_directions_link(latitude, longitude, aGeo[0], aGeo[1])
      #duration = RouteUtil.get_directions_duration(driver, directions_link)
      duration_minutes, directions_link = RouteUtil.get_directions_duration_minutes(driver, latitude, longitude, aGeo[0], aGeo[1])
      if (maxRouteTimeMinutes==0 or duration_minutes>=minRouteTimeMinutes) and (maxRouteTimeMinutes==0 or duration_minutes<=maxRouteTimeMinutes):
        conditionedMountains.add(aMountainName)
        if args.mountainNameOnly:
          break
        else:
          print(f'{aMountainName} {aGeo[0]} {aGeo[1]} {duration_minutes} {directions_link}')

  if args.mountainNameOnly:
    conditionedMountains = sorted(conditionedMountains)
    print( " ".join(conditionedMountains) )
