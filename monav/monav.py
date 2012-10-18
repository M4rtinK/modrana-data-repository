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

from repository import Package, Repository
import csv

SOURCE_DATA_URLS = "osm_pbf_extracts.csv"

class MonavRepository(Repository):
  def __init__(self):
    Repository.__init__()

  def update(self):
    self._downloadData()

  def _loadData(self, sourceQueue):
    pass

  def _processPackage(self, sourceQueue, packQueue):
    pass

  def _packagePackage(self, packQueue, publishQueue):
    pass

  def _publishPackage(self, publishQueue):
    pass



class MonavPackage(Package):
  def __init__(self, url):
    Package.__init__()