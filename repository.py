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

class Repository(object):
  def __init__(self):
    pass

class Package(object):
  # states

  DOWNLOADING = 1
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

  def getName(self):
    return self.name

  def getPath(self):
    return self.path

  def getState(self):
    return self.state

  def clear(self):
    """remove any data in storage created by this package"""
    pass


def main(self):
  print("starting repository update")