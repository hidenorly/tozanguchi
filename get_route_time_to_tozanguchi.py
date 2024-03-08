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



tozanguchiDic = tozanguchiDic.getTozanguchiDic()


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

  mountainKeys = set()
  mountains = set( args.args )
  mountains = MountainFilterUtil.mountainsIncludeExcludeFromFile( mountains, args.exclude, args.include )

  if len(mountains) == 0:
    parser.print_help()
    exit(-1)

  for aMountain in mountains:
    keys = TozanguchiUtil.getMountainKeys(aMountain)
    for aMountainKey in keys:
      mountainKeys.add( aMountainKey )

  minRouteTimeMinutes = TozanguchiUtil.getMinutesFromHHMM(args.minTime)
  maxRouteTimeMinutes = TozanguchiUtil.getMinutesFromHHMM(args.maxTime)

  pattern = r'(\d+\.\d+)\s+(\d+\.\d+)'
  match = re.search(pattern, str(args.longitudelatitude))
  if match:
  	print(f'{match.group(1)} {match.group(2)}')


  excludes = MountainFilterUtil.getSetOfCsvs( args.exclude )
  mountainNames = set()
  urlMap = {}
  parkInfo = None
  for aMountain in mountainKeys:
    if not MountainFilterUtil.isMatchedMountainRobust( excludes, aMountain ):
      tozanguchi = tozanguchiDic[aMountain]
      result = {}
      for aTozanguchi, theUrl in tozanguchi.items():
        parkInfo = TozanguchiUtil.getParkInfo(theUrl, args.renew, False)
        if parkInfo != None and TozanguchiUtil.isAcceptableTozanguchi( aMountain, parkInfo):
          result [ aTozanguchi ] = parkInfo
          urlMap[ str(parkInfo) ] = theUrl
