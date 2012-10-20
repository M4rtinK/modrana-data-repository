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
import shutil
import subprocess
import urllib2
import csv
import urlparse
import os

from core.package import Package
from core.repo import Repository
import core.repo as repo
import core.utils as utils

SOURCE_DATA_URLS_CSV = "osm_pbf_extracts.csv"

PREPROCESSOR_PATH = "monav-preprocessor"

class MonavRepository(Repository):
  def __init__(self, manager):
    Repository.__init__(self, manager)
    conf = manager.getConfig()
    self.preprocessorPath = conf.get('monav_preprocessor_path', PREPROCESSOR_PATH)

  def getName(self):
    return "Monav"

  def getFolderName(self):
    return "monav"

  def _preUpdate(self):
    """make sure temporary & publishing folders exist"""
    if utils.createFolderPath(self.getTempPath()) == False:
      return False
    if utils.createFolderPath(self.getPublishPath()):
      return False
    return True

  def _loadData(self, sourceQueue):
    tempPath = self.getTempPath()
    reader = csv.reader(SOURCE_DATA_URLS_CSV)
    print('monav loader: starting')
    packId = 0
    for row in reader:
      if len(row) > 0:
        url = row[0]
        try:
          pack = MonavPackage(url, tempPath, packId)
          packId+=1
          sourceQueue.put(pack)
        except Exception, e:
          print('monav loader: loading url failed: %s' % url)
          print(e)
    print('monav loader: all downloads finished')

  def _processPackage(self, sourceQueue, packQueue):
    """process OSM data in the PBF format into Monav routing data"""
    while True:
      package = sourceQueue.get()
      if package == repo.SHUTDOWN_KEYWORD:
        break
      # process the data
      package.process()
      # forward the package to the packaging pool
      packQueue.put(package)
    print('monav processing: shutting down')

  def _packagePackage(self, packQueue, publishQueue):
    """create a compressed TAR archive from the Monav routing data
    -> three packages (car, pedestrian, bike) are generated and compressed
    sequentially to three separate archives"""
    while True:
      package = packQueue.get()
      if package == repo.SHUTDOWN_KEYWORD:
        break
      # packaging
      package.package()
      # forward the package to the publishing process
      publishQueue.put(package)
    print('monav packaging: shutting down')

  def _publishPackage(self, publishQueue):
    """tak the compressed TARs and publish them to the modRana public folder
    and update the repository manifest accordingly"""
    while True:
      package = publishQueue.get()
      if package == repo.SHUTDOWN_KEYWORD:
        break
    print('monav publisher: shutting down')

class MonavPackage(Package):
  def __init__(self, url, tempPath, id, ):
    Package.__init__(self)
    self.url = url
    self.tempPath = tempPath
    self.id = id
    # get the storage path from the URL
    wholePath = urlparse.urlparse(url)[2]
    # split to filename & folder path
    self.repoPath, self.filename = os.path.split(wholePath)
    # get the filename without extensions
    self.name = self.filename.split('.')[0]
    # working directory during the processing phase
    self.tempStoragePath = os.path.join(tempPath, "%d" % id, self.name)
    # path to the source data file
    self.sourceDataPath = os.path.join(self.tempStoragePath, self.filename)
    # paths to resulting data files
    self.results = []

  def load(self):
    """download PBF extract from the URL and store it locally"""
    try:
      os.makedirs(self.tempStoragePath)
      request = urllib2.urlopen(self.url)
      f = open(self.sourceDataPath, "w")
      f.write(request.read())
      f.close()
      return True
    except Exception, e:
      message = 'monav package: OSM PBF download failed\n'
      message+= 'name: %s\n' % self.name
      message+= 'URL: %s\n' % self.url
      message+= 'storage path: %s' % self.sourceDataPath
      print(message)
      print(e)
      return False

  def process(self, threads=1):
    """process the PBF extract into Monav routing data"""
    try:
      inputFile = self.sourceDataPath
      outputFolder = self.tempStoragePath

      # first pass - import data, create address info & generate car routing data
      args1 = ['monav-preprocessor', '-di', '-dro="car"', '-t=%d' % threads, '--verbose', '--settings="base.ini"',
               '--input="%s"' % inputFile, '--output="%s"' % outputFolder, '--name="%s"' % self.name, '--profile="motorcar"']
      # second pass - import data, generate bike routing data
      args2 = ['monav-preprocessor', '-di', '-dro="bike"', '-t=%d' % threads, '--verbose', '--settings="base.ini"',
               '--input="%s"' % inputFile, '--output="%s"' % outputFolder, '--name="%s"' % self.name, '--profile="bicycle"']
      # third pass - import data, process pedestrian routing data & delete temporary files
      args3 = ['monav-preprocessor', '-di', '-dro="pedestrian"', '-t=%d' % threads, '--verbose', '--settings="base.ini"',
               '--input="%s"' % inputFile, '--output="%s"' % outputFolder, '--name="%s"' % self.name, '--profile="foot"', '-dd']

      # convert the arguments to whitespace delimited strings and run them
      subprocess.call(reduce(lambda x, y: x + " " + y, args1), shell=True)
      subprocess.call(reduce(lambda x, y: x + " " + y, args2), shell=True)
      subprocess.call(reduce(lambda x, y: x + " " + y, args3), shell=True)
      return True
    except Exception, e:
      message = 'monav package: Monav routing data processing failed\n'
      message+= 'name: %s' % self.name
      print(message)
      print(e)
      return False

  def package(self):
    """compress the Monav routing data"""
    modes = ["car", "bike", "pedestrian"]
    for mode in modes:
      path = os.path.join(self.tempStoragePath, "routing_%s" % mode)
      archivePath = os.path.join(self.tempStoragePath, "%s_%s.tar.gz" % (self.name, mode))
      try:
        utils.tarDir(path, archivePath)
        #TODO: MD5 hash for archives
        self.results.append(archivePath)
      except Exception, e:
        message = 'monav package: compression failed\n'
        message+= 'path: %s' % path
        message+= 'archive: %s' % archivePath
        print(message)
        print(e)

  def publish(self, targetPath, cleanup=False):
    """publish the package to the online repository"""
    for path2file in self.results:
      try:
        shutil.move(path2file, targetPath)
      except Exception, e:
        message = 'monav package: publishing failed\n'
        message+= 'file: %s' % path2file
        message+= 'target path: %s' % targetPath
        print(message)
        print(e)
    if cleanup: # clean up any source & temporary files
      self.clearSource()
      self.clearResults()