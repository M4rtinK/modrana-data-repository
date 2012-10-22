#!/usr/bin/python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Geofabrik PBF link extractor, part of the modRana data repository project
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