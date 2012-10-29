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
import time

from monav import MonavRepository, PREPROCESSOR_PATH, SOURCE_DATA_URLS_CSV
from core.configobj.configobj import ConfigObj
from core import repo
from core import utils
from core import startup

# keywords
SHUTDOWN_KEYWORD = "shutdown"
# folders
TEMP_PATH = "temp"
RESULTS_PATH = "results"
CONFIG_FILE_PATH = "repository.conf"

class Manager(object):
  """manages the overall repository state, including updating all
  sub-repositories"""
  def __init__(self):
    # load the configuration file
    self.conf = ConfigObj(CONFIG_FILE_PATH)
    self.args = startup.Startup().getArgs()

    # for now, update all repositories
    self.updateAll()

  def updateAll(self):

    print("## starting repository update ##")

    print("## updating Monav repository" )
    start = time.time()
    monav = MonavRepository(self)
    monav.update()
    dt = int(time.time() - start)
    if dt > 60:
      prettyTime = "%s (%d s)" % (utils.prettyTimeDiff(dt), dt)
      # show seconds for exact benchmarking once pretty time
      # switches to larger units
    else:
      prettyTime = utils.prettyTimeDiff(dt)
    print("## Monav repository updated in %s " % prettyTime)

    print("## repository update finished ##")

  def getConfig(self):
    """return parsed config file"""
    return self.conf

  def getArgs(self):
    """return the CLI options dictionary"""
    return self.args

  # Configuration variable wrappers

  def getConfigPath(self):
    """get configuration file path"""
    if self.args.c is not None:
      return self.args.c
    else:
      return repo.CONFIG_FILE_PATH

  def getTempPath(self):
    """temporary folder path wrapper"""
    return self._wrapVariable(self.args.temp_folder, "temporary_folder", repo.TEMP_PATH)

  def getRepoPath(self):
    """repository folder path wrapper"""
    return self._wrapVariable(self.args.repository_folder, "repository_folder", repo.RESULTS_PATH)

  def getCpuCount(self):
    """cpu count wrapper"""
    return self._wrapVariable(self.args.cpu_count, "cpu_count", mp.cpu_count())

  def getSourceQueueSize(self):
    """source queue size wrapper"""
    return self._wrapVariable(self.args.source_queue_size, "source_queue_size", repo.QUEUE_SIZE)

  def getPackagingQueueSize(self):
    """packaging queue size wrapper"""
    return self._wrapVariable(self.args.packaging_queue_size, "packaging_queue_size", repo.QUEUE_SIZE)

  def getPublishQueueSize(self):
    """publishing queue size wrapper"""
    return self._wrapVariable(self.args.publish_queue_size, "publish_queue_size", repo.QUEUE_SIZE)

  def getProcessingPoolSize(self):
    """processing pool size wrapper"""
    return self._wrapVariable(self.args.processing_pool_size, "processing_pool_size", repo.QUEUE_SIZE)

  def getPackagingPoolSize(self):
    """packaging pool size wrapper"""
    return self._wrapVariable(self.args.packaging_pool_size, "packaging_pool_size", repo.QUEUE_SIZE)

  # Monav variable wrappers

  def getMonavPreprocessorPath(self):
    """Monav preprocessor path wrapper"""
    return self._wrapVariable(self.args.monav_preprocessor_path, "monav_preprocessor_path", PREPROCESSOR_PATH)

  def getMonavPreprocessorThreads(self):
    """Monav preprocessor thread count wrapper"""
    cpuCount = int(self.getCpuCount())
    return self._wrapVariable(self.args.monav_preprocessor_threads, "monav_preprocessor_threads", max(1, cpuCount/4))

  def getMonavParallelThreads(self):
    """Monav preprocessor parallel thread count wrapper
    -> how many preprocessors would be run in parallel"""
    return self._wrapVariable(self.args.monav_parallel_threads, "monav_parallel_threads", 1)

  def getMonavParallelThreshold(self):
    """Monav preprocessor parallel run threshold wrapper
    -> don't run monav preprocessors in parallel is source data is larger than threshold"""
    return self._wrapVariable(self.args.monav_parallel_threshold, "monav_parallel_threshold", None)

  def getMonavCSVPath(self):
    """path to a CSV file with links to PBF extracts for Monav wrapper"""
    return self._wrapVariable(self.args.monav_csv_path, "monav_csv_path", SOURCE_DATA_URLS_CSV)

  def _wrapVariable(self, option, confKey, default):
    if option is not None:
      return option
    else:
      return self.conf.get(confKey, default)

if __name__ =='__main__':
  Manager()


