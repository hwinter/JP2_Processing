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

fontpath = "BebasNeue Regular.otf"
font = ImageFont.truetype(fontpath, 76)

target_wavelengths = ["94", "171", "193", "211", "304", "335"]
current_wavelength = ""

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
	convert_out = str(FILE).split(".")[0] + "-" + str(sorted_number) + ".png"
	subprocess.call("convert " + str(FILE) + " colortables/" + str(current_wavelength) + "_color_table.png -clut " + convert_out, shell = True)
	Annotate(convert_out)

def Annotate(FILE):
	print("FILE: " + str(FILE))

	date = 0
	time = 0
	wavelength = 0

	b,g,r,a = 191,191,191,0
	# framenum = database.index(FILE)
	# framenum = str(framenum).zfill(4)

	# print("FRAMENUM: " + str(framenum))

	print("ANNOTATING: " + str(FILE))
				
	date = str(FILE).split("__")[0].split("/")[1].replace("_", "-")
	time = str((FILE).split("__")[1])[:8].replace("_", ":")
	# date = "DATE"
	# time = "TIME"
	img = FILE
 
	img_pil = Image.open(FILE)
	# 	# Convert to RGB mode. Do I want to do this? I should maybe try RGBA
	if img_pil.mode != "RGB":
		img_pil = img_pil.convert("RGB")
	#	# Render it to a frame
	draw = ImageDraw.Draw(img_pil)
	# 	# #Put our text on it
	print("applying timestamp... ")
	draw.text((3468, 386), str(date), font = font, fill = (b, g, r, a))
	draw.text((3468, 456), str(time), font = font, fill = (b, g, r, a))
	draw.text((102, 3685), "Earth Added for Size Scale", font = ImageFont.truetype(fontpath, 56), fill = (b, g, r, a))
	# 	# #Turn it back in to a numpy array for OpenCV to deal with
	frameStamp = np.array(img_pil)
	annotate_out = "numbered/" + FILE.split("-")[1]

	# print("printing frame: " + str(framenum))
	cv2.imwrite(annotate_out, cv2.cvtColor(frameStamp, cv2.COLOR_RGB2BGR)) #It's critical to convert from BGR to RGB here, because OpenCV sees things differently from everyone else


for wlen in target_wavelengths:
	sorted_list = Fits_Index(str(wlen))
	sorted_list = AIA_DecimateIndex(sorted_list, 16)

	current_wavelength = wlen
	

	if os.path.isdir("numbered") == False:
		subprocess.call("mkdir numbered" , shell = True)
	else:
		for file in glob.glob("numbered/*.png"):
			os.remove(file)

	# sorted_number = 0

	# for f in sorted_list:
	# 	Colorize(f)


	# Using multiprocess.pool() to parallelize our frame rendering
	start = datetime.datetime.now()

	pool = Pool()
	pool.map(Colorize, sorted_list)
	pool.close()
	pool.join()

	finish = datetime.datetime.now()
	frame_timer = finish - start

	start = datetime.datetime.now()
	subprocess.call("ffmpeg -r 24 -i numbered/%01d.png -vcodec libx264 -b:v 20M -pix_fmt yuv420p -y jp2_test_" + str(wlen) + ".mp4", shell = True)
	finish = datetime.datetime.now()

	render_timer = finish - start
	print("TOTAL FRAMES: " + str(len(sorted_list)))
	print("PROCESSING TIME: " + str(frame_timer))
	print("RENDERING TIME: " + str(render_timer))




