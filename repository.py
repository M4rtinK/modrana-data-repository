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
from core.configobj.configobj import ConfigObj
from core import utils

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
    self.args = None # TODO: CLI options handling

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


if __name__ =='__main__':
  Manager()


