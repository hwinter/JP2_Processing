from __future__ import print_function

import matplotlib
matplotlib.use('agg')

from moviepy.editor import *
from moviepy.video.tools.segmenting import findObjects
from PIL import ImageFont, ImageDraw, Image
from astropy.io import fits
from sys import stdout as stdout
from numba import jit
from multiprocessing import Pool

import numpy as np
import sunpy.instr.aia as aia
import matplotlib.pyplot as plt

import cv2
import subprocess
import glob
import os
import datetime
import sys


def Fits_Index(DIR):
	fits_list = []
	count = 0
	for fits_file in sorted(glob.glob(DIR + "/*.jp2")):
		print("\r Adding file: " + str(fits_file) + " Entries: " + str(count), end = " ")
		fits_list.append(str(fits_file))
		count = count + 1
	print(fits_list) 
	return(fits_list)

def AIA_DecimateIndex(LIST, SKIP):
	list_in = LIST
	print("DECIMATING")
	list_out = [list_in[i] for i in xrange(0, len(list_in), SKIP)]

	return(list_out)

def Colorize(FILE):
	sorted_number = sorted_list.index(FILE)
	print("CONVERTING: " + str(FILE))
	subprocess.call("convert " + str(FILE) + " gradient_304.png -clut numbered/" + str(sorted_number) + ".png", shell = True)
	


sorted_list = Fits_Index("working")
sorted_list = AIA_DecimateIndex(sorted_list, 4)

if os.path.isdir("numbered") == False:
	subprocess.call("mkdir numbered" , shell = True)

# sorted_number = 0

# for f in sorted_list:
# 	print("CONVERTING: " + str(f))
# 	subprocess.call("convert " + str(f) + " gradient_ice-sea.png -clut numbered/" + str(sorted_number) + ".png", shell = True)
# 	sorted_number += 1

# Using multiprocess.pool() to parallelize our frame rendering
start = datetime.datetime.now()

pool = Pool()
pool.map(Colorize, sorted_list)
pool.close()
pool.join()

finish = datetime.datetime.now()
frame_timer = finish - start

start = datetime.datetime.now()
subprocess.call("ffmpeg -r 24 -i numbered/%01d.png -vcodec libx264 -b:v 4M -pix_fmt yuv420p -y jp2_test.mp4")
finish = datetime.datetime.now()

render_timer = finish - start
print("PROCESSING TIME: " + str(frame_timer))
print("RENDERING TIME: " + str(render_timer))




