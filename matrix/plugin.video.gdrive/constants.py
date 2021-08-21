'''
    gdrive (Google Drive ) for KODI / XBMC Plugin
    Copyright (C) 2013-2016 ddurdle

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.


'''

import re
import sys

from resources.lib import gdrive_api2

# cloudservice - standard XBMC modules
import xbmcaddon

PLUGIN_NAME = 'gdrive'

# global variables
addon = xbmcaddon.Addon(id='plugin.video.gdrive')

cloudservice2 = gdrive_api2.gdrive

class CONST():
	testing_features = False
	DEBUG = False