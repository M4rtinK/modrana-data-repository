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

  def getName(self):
    pass

  def getFolderName(self):
    """return folder name for the repository"""
    pass

  def update(self):
    # run pre-update
    if self._preUpdate() == False:
      print('repository pre-update failed')
      return False
    # start the loading process
    tempPath = self.getTempPath()
    self.loadingProcess = mp.Process(target=self._loadData, args=(self.sourceQueue,))
    self.loadingProcess.daemon = True
    self.loadingProcess.start()
    # start the processing processes
    for i in range(PROCESSING_POOL_SIZE):
      p = mp.Process(target=self._processPackage, args=(self.sourceQueue, self.packagingQueue))
      p.daemon = True
      p.start()
    # start the packaging processes
    for i in range(PROCESSING_POOL_SIZE):
      p = mp.Process(target=self._packagePackage, args=(self.packagingQueue, self.publishQueue))
      p.daemon = True
      p.start()
#    # start the publishing process
    self.publishingProcess = mp.Process(target=self._publishPackage, args=(self.publishQueue,),)
    self.publishingProcess.daemon = True
    self.publishingProcess.start()
    self.publishingProcess.join()
    # as the publishing process is the last one to handle work related to the update,
    # we join it to wait for the repository update to finish

    # run post-update
    if self._postUpdate() == False:
      print('repository post-update failed')
      return False
    return True

  def _preUpdate(self):
    """this method is called before starting the repository update"""
    pass

  def _postUpdate(self):
    """this method is called after finishing the repository update """
    pass


  ## Multiprocessing tasks ##
  def _loadData(self, sourceQueue):
    pass

  def _processPackage(self, sourceQueue, packQueue):
    pass

  def _packagePackage(self, packQueue, publishQueue):
    pass

  def _publishPackage(self, publishQueue):
    pass


  ## Paths ##
  def getTempPath(self):
    return os.path.join(TEMP_PATH, self.getFolderName())

  def getPublishPath(self):
    return os.path.join(RESULTS_PATH, self.getFolderName())

