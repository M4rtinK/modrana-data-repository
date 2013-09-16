#!/usr/bin/python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Geofabrik conutry polygon link extractor, part of the modRana data repository project
#----------------------------------------------------------------------------
# Copyright 2012, Martin Kolman
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#---------------------------------------------------------------------------

import httplib2
from BeautifulSoup import BeautifulSoup, SoupStrainer
import os
import urlparse

http = httplib2.Http()

BASE_URL = 'http://download.geofabrik.de/'
STARTING_URL = BASE_URL
DATA_URLS = {
  BASE_URL + 'africa',
  BASE_URL + 'antarctica',
  BASE_URL + 'asia',
  BASE_URL + 'australia-oceania',
  BASE_URL + 'central-america',
  BASE_URL + 'europe',
  BASE_URL + 'north-america',
  BASE_URL + 'south-america',
}

visited = set() # tracks visited urls to prevent an infinite loop
seen_PBFs = set() # track already seen PBFs

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

def is_valid(url):
  # first prevent the recursive
  # parsing from exiting the geofabrik domain
  if not url.startswith(BASE_URL):
    return False
  # skip the updates folders
  if "-updates" in url:
    return False


  for url in DATA_URLS:
    if url.startswith(url):
      return True
  return False

def checkUrl(url):
  """* if an url is a pbf file, print it and return None
  * if and url is inside the STARTING_URL prefix, return it
  * if it is outside, return None"""
  #print "URL " + url

  if is_valid(url):
    # check if it is a PBF file

    path, ext = os.path.splitext(url)
    if ext:
      if ext == '.pbf':
        # only get the latest PBF files
        if url.endswith("-latest.osm.pbf") and url not in seen_PBFs:
          # add the url to the set of already found urls
          # to prevent printing out duplicates
          seen_PBFs.add(url)
          print url
        else:
          return None
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