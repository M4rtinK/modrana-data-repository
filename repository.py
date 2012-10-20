#!/usr/bin/python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# modRana data repository - core
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

import multiprocessing as mp
import os
import time

from monav import MonavRepository
import ConfigParser

# pool & queue sizes
CPU_COUNT = mp.cpu_count()
QUEUE_SIZE = CPU_COUNT*2
SOURCE_DATA_QUEUE_SIZE = QUEUE_SIZE
PROCESSING_POOL_SIZE = CPU_COUNT
PACKAGING_QUEUE_SIZE = QUEUE_SIZE
PACKAGING_POOL_SIZE = CPU_COUNT
PUBLISHING_QUEUE_SIZE = QUEUE_SIZE
# keywords
SHUTDOWN_KEYWORD = "shutdown"
# folders
TEMP_PATH = "temp"
RESULTS_PATH = "results"
CONFIG_FILE_PATH = "repository.conf"

class Repository(object):
  def __init__(self, manager):
    self.manager = manager

    # is fed by the data loader
    self.sourceQueue = mp.Queue(SOURCE_DATA_QUEUE_SIZE)
    # the processing pool consumes from the source queue
    self.processingPool = mp.Pool(CPU_COUNT)
    self.packagingQueue = mp.Queue(PACKAGING_QUEUE_SIZE)
    self.packagingPool = mp.Pool(CPU_COUNT)
    self.publishQueue = mp.Queue(PUBLISHING_QUEUE_SIZE)

    self.loadingProcess = None
    self.publishingProcess = None

  def update(self):
    # start the loading process
    tempPath = self.getTempPath()
    self.loadingProcess = mp.Process(target=self._loadData, args=(tempPath, self.sourceQueue))
    # start the processing processes
    self.processingPool.apply_async(func=self._processPackage, args=(self.sourceQueue, self.packagingQueue))
    # start the packaging processes
    self.processingPool.apply_async(func=self._packagePackage, args=(self.packagingQueue, self.publishQueue))
    # start the publishing process
    self.publishingProcess = mp.Process(target=self._loadData, args=self.publishQueue)

  def _loadData(self, sourceQueue):
    pass

  def _processPackage(self, sourceQueue, packQueue):
    pass

  def _packagePackage(self, packQueue, publishQueue):
    pass

  def _publishPackage(self, publishQueue):
    pass

  def _getFolderName(self):
    pass

  def getTempPath(self):
    return os.path.join(TEMP_PATH, self._getFolderName())

  def getResultsPath(self):
    return os.path.join(RESULTS_PATH, self._getFolderName())

class Package(object):
  # states

  LOADING = 1
  PROCESSING = 2
  DONE = 3

  def __init__(self):
    self.name = None
    self.size = None
    # this timestamp relates to when
    # the source data were last updated
    self.dataTimestamp = None
    # path to the data folder
    self.path = None
    self.state = None
    # combined time spend on package processing in seconds
    self.processingTime = 0
    # current loading progress 0.0 = 0%, 1.0 = 100%
    self.loadingProgress = 0.0

  def getName(self):
    return self.name

  def getPath(self):
    return self.path

  def getState(self):
    return self.state

  def getLoadingProgress(self):
    return self.loadingProgress

  def _addProcessingTime(self, pTime):
    self.processingTime+=pTime

  def getProcessingTime(self):
    """return how long this package took to process so far in seconds"""
    return self.processingTime

  def _timeit(self, fn):
    def wrapped():
      start = time.time()
      fn()
      self._addProcessingTime(time.time()- start)
    return wrapped

  def load(self):
    pass


  def process(self):
    pass

  def package(self):
    pass

  def clearSource(self):
    """remove any source data for this package"""
    pass

  def clearResults(self):
    """remove any result data for this package"""
    pass

class Manager(object):
  """manages the overall repository state, including updating all
  sub-repositories"""
  def __init__(self):
    # load the configuration file
    self.conf = ConfigParser.ConfigParser()
    self.conf.read(CONFIG_FILE_PATH)
    self.args = None # TODO: CLI options handling

    # for now, update all repositories
    self.updateAll()

  def updateAll(self):

    print("## starting repository update ##")

    print("## updating Monav repository" )
    start = time.clock()
    monav = MonavRepository(self)
    monav.update()
    dt = int(time.clock - start)
    print("## Monav repository updated in %d s" % dt)

  def getConf(self):
    """return parsed config file"""
    return self.conf

  def getArgs(self):
    """return the CLI options dictionary"""
    return self.args


if __name__ =='__main__':
  Manager()


