#!/usr/bin/python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Monav data repository
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
import urllib
import urllib2

from repository import Package, Repository
import csv
import urlparse
import os

SOURCE_DATA_URLS_CSV = "osm_pbf_extracts.csv"

class MonavRepository(Repository):
  def __init__(self):
    Repository.__init__()

  def update(self):
    self._downloadData()

  def _loadData(self, tempPath, sourceQueue):
    reader = csv.reader(SOURCE_DATA_URLS_CSV)
    print('monav loader: starting')
    packId = 0
    for row in reader:
      if len(row) > 0:
        try:
          url = row[0]
          pack = MonavPackage(url, tempPath, id)
          id+=1
          sourceQueue.put(pack)

        except Exception, e:
          print('monav loader: loading url failed: %s' % url)
          print(e)


    print('monav loader: finished')


  def _processPackage(self, sourceQueue, packQueue):
    pass

  def _packagePackage(self, packQueue, publishQueue):
    pass

  def _publishPackage(self, publishQueue):
    pass

class MonavPackage(Package):
  def __init__(self, url, tempPath, id):
    Package.__init__()
    self.url = url
    self.tempPath = tempPath
    self.id = id
    # get the storage path from the URL
    wholePath = urlparse.urlparse(url)[2]
    # split to filename & folder path
    self.repoPath, self.filename = os.path.split(wholePath)
    # get the filename without extensions
    self.name = self.filename.split('.')[0]
    self.tempStoragePath = os.path.join(tempPath, "%d" % id, self.name)
    self.sourceDataPath = os.path.join(self.tempStoragePath, self.filename)
  def startLoading(self):
    """download PBF extract from the URL and store it locally"""
    os.makedirs(self.tempStoragePath)
    request = urllib2.urlopen(self.url)
    f = open(self.sourceDataPath, "w")
    f.write(request.read())
    f.close()

