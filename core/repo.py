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
QUEUE_SIZE = 10
SOURCE_DATA_QUEUE_SIZE = QUEUE_SIZE
PROCESSING_POOL_SIZE = CPU_COUNT
PACKAGING_QUEUE_SIZE = QUEUE_SIZE
PACKAGING_POOL_SIZE = CPU_COUNT
PUBLISHING_QUEUE_SIZE = QUEUE_SIZE
# keywords
SHUTDOWN_SIGNAL = "shutdown"
# folders
TEMP_PATH = "temp"
RESULTS_PATH = "results"
CONFIG_FILE_PATH = "repository.conf"
# URL types
GEOFABRIK_URL = 1

class Repository(object):
  def __init__(self, manager):
    self.manager = manager

    # the source queue is fed by the data loader
    self.sourceQueue = mp.JoinableQueue(manager.getSourceQueueSize())
    # the packaging queue is fed by the processing processes
    self.packagingQueue = mp.JoinableQueue(manager.getPackagingQueueSize())
    # the publishing queue is fed by the packaging processes
    self.publishQueue = mp.JoinableQueue(manager.getPublishQueueSize())

    # loads data for processing
    self.loadingProcess = None
    # publishes packages to online repository
    self.publishingProcess = None

  def getName(self):
    """return a pretty name for the repository"""
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
    for i in range(self.getProcessingPoolSize()):
      p = mp.Process(target=self._processPackage, args=(self.sourceQueue, self.packagingQueue))
      p.daemon = False
      p.start()
    # start the packaging processes
    for i in range(self.getPackagingPoolSize()):
      p = mp.Process(target=self._packagePackage, args=(self.packagingQueue, self.publishQueue))
      p.daemon = True
      p.start()
    # start the publishing process
    self.publishingProcess = mp.Process(target=self._publishPackage, args=(self.publishQueue,),)
    self.publishingProcess.daemon = True
    self.publishingProcess.start()

    # start a method that first joins the first process, once it stops it joins
    # all the queues in sequence and feeds them with shutdown commands corresponding to the number of
    # worker processes corresponding to the given Queue
    # -> this shut shut-down the whole operation in sequence on the individual stages dry up
    self._terminateOnceDone()

    # run post-update
    if self._postUpdate() == False:
      print('repository post-update failed')
      return False
    return True

  def _terminateOnceDone(self):
    """terminate processes through their input queue
    once the previous stage runs out of work"""
    # first wait fo the loader to finish
    self.loadingProcess.join()

    # then shut down all the stages in sequence as they run out of work
    stages = [
      (self.sourceQueue, self.getProcessingPoolSize()),
      (self.packagingQueue, self.getPackagingPoolSize()),
      (self.publishQueue, 1)
    ]

    for queue, processCount in stages:
      # join the queue and wait for any work units to be finished
      queue.join()
      # now send to shutdown commands to the processes feeding from the queue
      for i in range(processCount):
        queue.put(SHUTDOWN_SIGNAL)
      # wait for the shutdown signals to be processed
      queue.join()

  def getProcessingPoolSize(self):
    """returns the number of threads to start in the data processing pool
    NOTE: this number should not change once the processing threads are started,
    as it might prevent a clean shutdown"""
    return self.manager.getProcessingPoolSize()

  def getPackagingPoolSize(self):
    """returns the number of threads to start in the data packaging pool
    NOTE: this number should not change once the packaging threads are started,
    as it might prevent a clean shutdown"""
    return self.manager.getPackagingPoolSize()

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
    return os.path.join(
      self.manager.getTempPath(),
      self.getFolderName())

  def getPublishPath(self):
    return os.path.join(
      self.manager.getRepoPath(),
      self.getFolderName())

  ## Source data URLs ##
  def _getSourceUrlType(self):
    # TODO: config file switch for setting this,
    # so that using the URL verbatim is possible
    return GEOFABRIK_URL
