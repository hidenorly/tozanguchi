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

import time
import sys
import requests
from bs4 import BeautifulSoup

def isMountainLink(url):
  return url.find("trailhead/trailhead")!=-1

def getUniqueKey(hashmap, key):
  if key in hashmap:
    countIndex = key.rfind("_")
    if countIndex != -1:
      count = int( key[countIndex+1:key.len()] ) + 1
      key = key[0:countIndex+1]+str(count)
    else:
      key = key+"_2"
  return key

def getUniqueKeyValue(hashmap, key, value):
  if key in hashmap:
    if hashmap[key]!=value:
      countIndex = key.rfind("_")
      if countIndex != -1:
        count = int( key[countIndex+1:key.len()] ) + 1
        key = key[0:countIndex+1]+str(count)
      else:
        key = key+"_2"
  return key

def getMountainName(name):
  index = name.find("（")
  if( index!=-1 ):
    name = name[0:index]
  index = name.find("\xa0")
  if( index!=-1 ):
    name = name[0:index]
  index = name.find("(")
  if( index!=-1 ):
    name = name[0:index]
  return name.strip()

def getLinks(articleUrl, result):
  if result == None:
    result = {}
  res = requests.get(articleUrl)
  soup = BeautifulSoup(res.text, 'html.parser') #use html instead of res.text
  article = soup.find("article", {})
  if None != article:
      mountains = article.find_all("h3")
      mountainNames = []
      for aMountain in mountains:
        mountainNames.append( getMountainName( aMountain.get_text().strip() ) )
      mountainMax = len(mountainNames)
      tozanguchis = article.find_all("p", {"class":"th_data"})
      i = 0
      for aTozanguchi in tozanguchis:
        theLinks = aTozanguchi.find_all("a")
        theMountainName = ""
        if i<mountainMax:
          theMountainName = mountainNames[i]
          i=i+1
        tozanguchis = {}
        for aTozanguchiLink in theLinks:
          theUrl = aTozanguchiLink.get("href").strip()
          theText = aTozanguchiLink.get_text().strip()
          if isMountainLink(theUrl):
            tozanguchis[getUniqueKeyValue(tozanguchis, theText, theUrl)] = theUrl
        result[ getUniqueKey(result, theMountainName) ] = tozanguchis
  return result


if __name__=="__main__":
  links={}
  if len(sys.argv) == 5:
    if sys.argv[1].startswith("http"):
      links = getLinks(sys.argv[1], links)
    if sys.argv[2].startswith("http"):
      targetLink = sys.argv[2]
      i=int(sys.argv[3])
      maxPages = int(sys.argv[4])
      while i<=maxPages:
        time.sleep(1)
        links = getLinks(targetLink+str(i), links)
        i=i+1

    print("tozanguchiDic={")
    for theText, theUrl in links.items():
      if isinstance(theUrl, dict):
        print('  "'+theText+'":{')
        for tozanguchi, link in theUrl.items():
          print('    "'+tozanguchi + '":"' +link+'",')
        print('  }')
    print("}")

    print('''
def getTozanguchiDic():
  return tozanguchiDic
''')