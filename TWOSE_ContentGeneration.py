# -*- coding: utf-8 -*-
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
import requests

global_date = datetime.datetime.now()
global_date = str(global_date)
year = global_date.split("-")[0]
month = global_date.split("-")[1]
day = str(int(global_date.split("-")[2].split(" ")[0]) - 1).zfill(2)

fontpath = "BebasNeue Regular.otf"
font = ImageFont.truetype(fontpath, 76)

target_wavelengths = ["94", "171", "193", "211", "304", "335"]
temperatures_celsius = ["6,000,000 degrees Celsius", "1,000,000 degrees Celsius", "1,222,200 degrees Celsius", "2,000,000 degrees Celsius", "100,000 degrees Celsius", "2,500,000 degrees Celsius"]
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
	subprocess.call('ffmpeg -i ' + str(convert_out) + ' -vf "scale=(iw*sar)*min(4854/(iw*sar)\,4096/ih):ih*min(4854/(iw*sar)\,4096/ih), pad=4854:4096:(4854-iw*min(4854/iw\,4096/ih))/2:(4096-ih*min(4096/iw\,4096/ih))/2"  -y ' + str(convert_out), shell = True)

	Annotate(convert_out)

def Annotate(FILE):
	print("FILE: " + str(FILE))

	date = 0
	time = 0
	wlen = 0

	b,g,r,a = 191,191,191,0
	# framenum = database.index(FILE)
	# framenum = str(framenum).zfill(4)

	# print("FRAMENUM: " + str(framenum))

	print("ANNOTATING: " + str(FILE))
				
	date = str(FILE).split("__")[0].split("/")[1].replace("_", "-")
	time = str((FILE).split("__")[1])[:8].replace("_", ":")
	wlen = str(FILE).split(".")[0].split("__")[2].split("_")[3].split("-")[0]
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
	# print("applying timestamp... ")
	draw.text((102, 306), "Temperature:", font = ImageFont.truetype(fontpath, 90), fill = (b, g, r, a))
	draw.text((102, 386), temperatures_celsius[target_wavelengths.index(wlen)], font = font, fill = (b, g, r, a))
	draw.text((3868, 306), "Observation Time:", font = ImageFont.truetype(fontpath, 90), fill = (b, g, r, a))
	draw.text((3868, 386), str(date), font = font, fill = (b, g, r, a))
	draw.text((3868, 456), str(time), font = font, fill = (b, g, r, a))
	draw.text((102, 3705), "Earth Added for Size Scale", font = ImageFont.truetype(fontpath, 56), fill = (b, g, r, a))
	# 	# #Turn it back in to a numpy array for OpenCV to deal with
	frameStamp = np.array(img_pil)
	annotate_out = "numbered/" + FILE.split("-")[1]

	# print("printing frame: " + str(framenum))
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
	earth_g = earth_g.set_duration(earthvideo_length).fl_time(lambda t: speedmult*t).set_pos((102, 3635), relative = False).resize(0.07163) # to account for the downsized resolution of our template video. Current Earth size = 320 pixels


	#The above statement is the meat and potatos of this script.
	#SPEED: We use fl_time to match the rotational speed of earth to our timelapse. where t = realtime speed of the video, we multiply t by the ratio of our Earth gif's length (1 min) to our main video length, assuming that our main video is a 24 hour timelapse of varying speed.
	#SET POSITION: We use set_position() to position the Earth, using relative percentages of overall screen size. EG: 0.85, 0.85 means 85% of the way across the screen along the x and y axes.
	#RESIZE: resize() resizes our Earth gif by a percentage, in this case derived by Earth's diameter in pixels (407 in our Whiteboxed example) divided by the sun's (3178 at native AIA resolution). 
	#set_position() and resize() both accept lambda t: values, so our Earth gif can be resized and moved dynamically.

	main_video.extend( [earth_g] )
	out_video = CompositeVideoClip(main_video)

	out_video.set_duration(mlength).write_videofile(str(FILE).split(".")[0] + "_.mp4", fps = 24, threads = 2, audio = False, progress_bar = True)
	os.rename(str(FILE).split(".")[0] + "_.mp4", FILE)

##FROM AIA
def Video_List():
	videolist = []
	for f in sorted(glob.glob("working/wav_vids/*.mp4")):
		videolist.append(str(f))

	return videolist

def AIA_ArrangeByTemp(LIST):
	list_in = LIST
	list_order = [0, 5, 3 , 2, 1, 4]

	list_out = [list_in[i] for i in list_order]

	return(list_out)

def AIA_AddInfographic(BASE, OVERLAY, OUTNAME): #BASE: Output of AIA_GenerateBackground(), Overlay: the graphical overlay image EG: TWOSE_Wall_Base2x2.mp4, OVERLAY_2x2.png
	
	cap = cv2.VideoCapture(BASE)
	fg = cv2.imread(OVERLAY,-1)

	i = 0;

	while(cap.isOpened()):
	    ret, frame = cap.read()
	    if ret == True:

	        # Read the foreground image with alpha channel
	        foreGroundImage = fg

	        # Split png foreground image
	        b,g,r,a = cv2.split(foreGroundImage)

	        # Save the foregroung RGB content into a single object
	        foreground = cv2.merge((b,g,r))

	        # Save the alpha information into a single Mat
	        alpha = cv2.merge((a,a,a))

	        foreground = foreground.astype(float)

	        background = frame

	        # Convert uint8 to float
	        background = background.astype(float)
	        alpha = alpha.astype(float)/255

	        # Perform alpha blending
	        foreground = cv2.multiply(alpha, foreground)
	        background = cv2.multiply(1.0 - alpha, background)
	        outImage = cv2.add(foreground, background)

	        # write the processed frame

	        cv2.imwrite("TWOSE_out" + str(i) + ".png", outImage)
	        i = i + 1
	
	        print("\rOverlaying frame: " + str(i), end = "")
	        stdout.flush() 

	        if cv2.waitKey(1) & 0xFF == ord('q'):
	            break
	    else:
	        break

	subprocess.call('ffmpeg -r 24 -i TWOSE_out%01d.png -vcodec libx264 -b:v 4M -pix_fmt yuv420p -y ' + str(OUTNAME), shell=True)

	for f in glob.glob("TWOSE_out*.png"):
	    os.remove(f)

	# Release everything if job is finished
	cap.release()


for wlen in target_wavelengths:
	sorted_list = Fits_Index(str(wlen))
	sorted_list = AIA_DecimateIndex(sorted_list, 8)

	current_wavelength = wlen
	
	subprocess.call("rm " + str(wlen) + "/*.png", shell = True) #purge PNG files from previous runs. This is less than ideal, but neccessary until we solve the problem of shifting timeframes and corresponding frame numbers

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
	subprocess.call("ffmpeg -r 24 -i numbered/%01d.png -vcodec libx264 -b:v 4M -pix_fmt yuv420p -crf 18 -y working/wav_vids/" + str(wlen).zfill(4) + ".mp4", shell = True)
	Add_Earth("working/wav_vids/" + str(wlen).zfill(4) + ".mp4")
	"""
	The range of the CRF scale is 0–51, where 0 is lossless, 23 is the default, and 51 is worst quality possible. 
	A lower value generally leads to higher quality, and a subjectively sane range is 17–28. 
	Consider 17 or 18 to be visually lossless or nearly so; it should look the same or nearly the same as the input but it isn't technically lossless.
	"""
	finish = datetime.datetime.now()

	render_timer = finish - start
	print("TOTAL FRAMES: " + str(len(sorted_list)))
	print("PROCESSING TIME: " + str(frame_timer))
	print("RENDERING TIME: " + str(render_timer))


# Generate a base video composite -> add graphical overlay -> Repeat. Each overlay is numerically matched to the base video, to synchronize temperature data.

vlist = Video_List()
print("VLIST: " + str(vlist))
vlist = AIA_ArrangeByTemp(vlist)
print("SORTED: " + str(vlist))

# Take all the clips we've generated, and stitch them in to one long video.
clip1 = VideoFileClip(str(vlist[0]))
clip2 = VideoFileClip(str(vlist[1]))
clip3 = VideoFileClip(str(vlist[2]))
clip4 = VideoFileClip(str(vlist[3]))
clip5 = VideoFileClip(str(vlist[4]))
clip6 = VideoFileClip(str(vlist[5]))

final_outname = str(year) + "_" + str(month) + "_" + str(day) + "_TWOSE_VideoWall_Concatenated.mp4"

final_clip = concatenate_videoclips([clip6, clip5.crossfadein(1), clip4.crossfadein(1), clip3.crossfadein(1), clip2.crossfadein(1), clip1.crossfadein(1)], padding = -1, method = "compose")
final_clip.write_videofile("daily_mov/" + str(final_outname), fps = 24, threads = 4, audio = False, progress_bar = True)

# Cleanup the directory when we're done
# for f in glob.glob("TWOSE_BaseSegment_*.mp4"):
# 	    os.remove(f)

# for f in glob.glob("TWOSE_SegmentOverlay_*.mp4"):
# 	    os.remove(f)

# timeend = datetime.datetime.now()
# finaltime = timeend - timestart
# print("Final Runtime: " + str(finaltime))



