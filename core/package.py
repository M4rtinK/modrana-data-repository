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


