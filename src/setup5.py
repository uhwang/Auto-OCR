# -*- coding: utf-8 -*-

# A simple setup script to create an executable using PyQt4. This also
# demonstrates the method for creating a Windows executable that does not have
# an associated console.
#
# PyQt4app.py is a very simple type of PyQt4 application
#
# Run the build process by running the command 'python setup.py build'
#
# If everything works well you should find a subdirectory in the build
# subdirectory that contains the files needed to run the application

#http://www.py2exe.org/index.cgi/CustomIcons
#http://www.winterdrache.de/freeware/png2ico/

from distutils.core import setup
import py2exe
import sys
from glob import glob

sys.argv.append('py2exe')

#setup(windows=["encode.py"], options={"py2exe" : {"includes" : ["sip", "PyQt4", "youtube_dl"]}})

setup(
	name = 'Img2Pdf',
	version='0.1',
	description='Automate Crop & OCR',
	author='Uisang Hwang',
	windows=[{"script": 'img2pdf.py', "icon_resources": [(0, "img2pdf.ico")]}], 
    data_files=[
                ('platforms', glob(r'C:/Python/Lib/site-packages/PyQt5/Qt5/plugins/platforms\qwindows.dll')),
                ('', glob(r'C:/Python/Lib/site-packages/PyQt5/Qt5/bin/Qt5Core.dll')),
                ('', glob(r'C:/Python/Lib/site-packages/PyQt5/Qt5/bin/Qt5Gui.dll')),
                ('', glob(r'C:/Python/Lib/site-packages/PyQt5/Qt5/bin/Qt5Widgets.dll'))
               ],    
	options={'py2exe': {"dist_dir": "bin", 
              "includes" : ["PyQt5.sip"], 
              "excludes":["TKinter", "numpy", "pandas", "scipy", "matplotlib", "numba"]}},
    py_modules=[]
)