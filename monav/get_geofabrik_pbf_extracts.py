# Geofabrik pbf link extractor, parr of the modRana data repository project

import httplib2
from BeautifulSoup import BeautifulSoup, SoupStrainer
import os
import urlparse

http = httplib2.Http()

STARTING_URL = 'http://download.geofabrik.de/openstreetmap/'

visited = set() # tracks visited urls to prevent an infinite loop

def parsePage(url):
  """return all URLs from a given URL"""
  if url not in visited:
    links = []
    status, response = http.request(url)
    for link in BeautifulSoup(response, parseOnlyThese=SoupStrainer('a')):
      if link.has_key('href'):
        link = urlparse.urljoin(url, link['href'])
        if checkUrl(link):
          links.append(link)
    visited.add(url)
    return links
  else:
    return []

def checkUrl(url):
  """* if an url is a pbf file, print it and return None
  * if and url is inside the STARTING_URL prefix, return it
  * if it is outside, return None"""
  if url.startswith(STARTING_URL):
    path, ext = os.path.splitext(url)
    if ext:
      if ext == '.pbf':
        print url
      else:
        return None
    else:
      return url
  else:
    return None

def getLinks(urls):
  """call parsePage recursively"""
  for url in urls:
    getLinks(parsePage(url))

def main():
  getLinks([STARTING_URL])

main()