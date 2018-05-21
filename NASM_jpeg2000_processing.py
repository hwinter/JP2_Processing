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
from bs4 import BeautifulSoup

import numpy as np
import sunpy.instr.aia as aia
import matplotlib.pyplot as plt

import cv2
import subprocess
import glob
import os
import datetime
import sys
import requests

fontpath = "BebasNeue Regular.otf"
font = ImageFont.truetype(fontpath, 76)

target_wavelengths = ["94", "171", "193", "211", "304", "335"]
current_wavelength = str(input("WAVELENGTH: "))
year = str(input("YEAR: ")).zfill(4)
month = str(input("MONTH: ")).zfill(2)
day = str(input("DAY: ")).zfill(2)

def buildURL():
	wlen = current_wavelength
	urlout = "http://jsoc.stanford.edu/data/aia/images/" + str(year) + "/" + str(month) + "/" + str(day) + "/" + str(wlen) 
	return(urlout)

def listFD(url, ext=''):
    page = requests.get(url).text
    # print page
    soup = BeautifulSoup(page, 'html.parser')
    return [url + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(ext)]

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
	subprocess.call('ffmpeg -i ' + str(convert_out) + ' -vf "scale=(iw*sar)*min(4854/(iw*sar)\,4096/ih):ih*min(4854/(iw*sar)\,4096/ih), pad=4854:4096:(4854-iw*min(4854/iw\,4096/ih))/2:(4096-ih*min(4096/iw\,4096/ih))/2"  -y ' + str(convert_out), shell = True)
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
	print("applying text... ")
	draw.text((3468, 386), str(date), font = font, fill = (b, g, r, a))
	draw.text((3468, 456), str(time), font = font, fill = (b, g, r, a))
	draw.text((102, 386), "Lorem Ipsum Dolor Sit", font = font, fill = (b, g, r, a))
	draw.text((102, 456), "Sed Arctus Incam Hepter Scala", font = font, fill = (b, g, r, a))
	draw.text((102, 526), "Noli Em Ipicare Vera Solus", font = font, fill = (b, g, r, a))
	draw.text((102, 3120), "Earth Added for Size Scale", font = ImageFont.truetype(fontpath, 56), fill = (b, g, r, a))
	# 	# #Turn it back in to a numpy array for OpenCV to deal with
	frameStamp = np.array(img_pil)
	annotate_out = "numbered/" + FILE.split("-")[1]

	print("printing frame: " + annotate_out)
	cv2.imwrite(annotate_out, cv2.cvtColor(frameStamp, cv2.COLOR_RGB2BGR)) #It's critical to convert from BGR to RGB here, because OpenCV sees things differently from everyone else

def Add_Earth(FILE):
	print("ADDING EARTH TO: " + str(FILE))
	main_video = [VideoFileClip(FILE)]
	mainvideo_length = main_video[0].duration
	print("MAIN LENGTH: ", str(mainvideo_length))

	mlength = mainvideo_length

	earth_g = VideoFileClip("misc/Earth_WhiteBox_TBG.gif", has_mask = True, fps_source = "fps") #It's important to specify the FPS source here because otherwise Moviepy for some reason assumes it's not 24 fps, which skews our speed calculations later on.

	earthvideo_length = 60 #I'm having a problem with Moviepy (go figure) skipping to what seems to be an arbitrary frame at the very end of the video, rather than looping seemlessly. It also does not accurately measure the duration of the gif.
	print("EARTH LENGTH: ", str(earthvideo_length))

	speedmult = (earthvideo_length / mainvideo_length) #our Earth gif completes a full rotation in 60 seconds (to be completely accurate, it's 59.97. framerates). Here we're figuring out how much slower or faster the video needs to be to align our Earth rotation speed with the speed of our timelapse.
	print("SPEEDMULT: ", str(speedmult))

	# earth_g = earth_g.set_duration(earthvideo_length).fl_time(lambda t: speedmult*t).set_pos((0.7, 0.7), relative = True).resize(lambda t : 1-0.01*t)
	# earth_g = earth_g.set_duration(earthvideo_length).fl_time(lambda t: speedmult*t).set_position(lambda t: (0.85-t*0.1, 0.85-t*0.1), relative = True).resize(0.071)
	earth_g = earth_g.set_duration(earthvideo_length).fl_time(lambda t: speedmult*t).set_pos((0.024, 0.88), relative = True).resize(0.091) # to account for the downsized resolution of our template video. Current Earth size = 320 pixels


	#The above statement is the meat and potatos of this script.
	#SPEED: We use fl_time to match the rotational speed of earth to our timelapse. where t = realtime speed of the video, we multiply t by the ratio of our Earth gif's length (1 min) to our main video length, assuming that our main video is a 24 hour timelapse of varying speed.
	#SET POSITION: We use set_position() to position the Earth, using relative percentages of overall screen size. EG: 0.85, 0.85 means 85% of the way across the screen along the x and y axes.
	#RESIZE: resize() resizes our Earth gif by a percentage, in this case derived by Earth's diameter in pixels (407 in our Whiteboxed example) divided by the sun's (3178 at native AIA resolution). 
	#set_position() and resize() both accept lambda t: values, so our Earth gif can be resized and moved dynamically.

	main_video.extend( [earth_g] )
	out_video = CompositeVideoClip(main_video)

	out_video.set_duration(mlength).write_videofile("o_" + str(FILE), fps = 24, threads = 4, audio = False, progress_bar = True)
	os.rename("o_" + str(FILE),FILE)

#MAIN:

url = buildURL()
print("CHECKING: " + str(url))

alist = []
for file in listFD(url, 'jp2'):
    alist.append(str(file))

print(alist[len(alist)-1])

print("LENGTH: " + str(len(alist)))
frameskip = input("TIMELAPSE: ")
alist = AIA_DecimateIndex(alist, frameskip)
print(alist[len(alist)-1])
# wait = input("WAIT...")

for file in range(0, len(alist)):
	check = alist[file]
	print("CHECK: " + check)
	print("ECHO: " + "wget -P " + str(current_wavelength) + " " + check)
	
	subprocess.call("wget -P " + str(current_wavelength) + " " + check, shell = True)


sorted_list = Fits_Index(str(current_wavelength))
# sorted_list = AIA_DecimateIndex(sorted_list, 8)


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

outname = "NASM_" + year + month + day + ".mp4"

print("RENDERING: " + outname)

subprocess.call("ffmpeg -r 24 -i numbered/%01d.png -vcodec libx264 -b:v 4M -pix_fmt yuv420p -crf 18 -y " + outname, shell = True)
Add_Earth(outname)
# subprocess.call('ffmpeg -i ' + str(outname) + ' -vf "scale=(iw*sar)*min(3840/(iw*sar)\,3240/ih):ih*min(3840/(iw*sar)\,3240/ih), pad=3840:3240:(3840-iw*min(3840/iw\,3240/ih))/2:(3240-ih*min(3240/iw\,3240/ih))/2" ' + str(outname), shell = True)

finish = datetime.datetime.now()

render_timer = finish - start
print("TOTAL FRAMES: " + str(len(sorted_list)))
# print("PROCESSING TIME: " + str(frame_timer))
print("RENDERING TIME: " + str(render_timer))




