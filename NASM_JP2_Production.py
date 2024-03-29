# -*- coding: utf-8 -*-
from __future__ import print_function

import matplotlib
matplotlib.use('agg')

from moviepy.editor import *
from moviepy.video.tools.segmenting import findObjects
from PIL import ImageFont, ImageDraw, Image
# from astropy.io import image
from sys import stdout as stdout
from numba import jit
from multiprocessing import Pool

import numpy as np
#import sunpy.instr.aia as aia
import matplotlib.pyplot as plt

import cv2
import subprocess
import glob
import os
import datetime
import sys
import requests
import traceback

#import SendText

global_date = datetime.datetime.now()
global_date = str(global_date)
year = global_date.split("-")[0]
month = global_date.split("-")[1]
day = str(int(global_date.split("-")[2].split(" ")[0]) - 1).zfill(2)

fontpath = "misc/BebasNeue Regular.otf"
font = ImageFont.truetype(fontpath, 56)

target_wavelengths = ["94", "171", "193", "211", "304", "335"]
current_wavelength = ""

#Compiles a sorted list of JP2 files in a given directory
def Build_Index(DIR):
	image_list = []
	count = 0
	for image_file in sorted(glob.glob(DIR + "/*.jp2")):
		print("\r Adding file: " + str(image_file) + " Entries: " + str(count), end = " ")
		image_list.append(str(image_file))
		count = count + 1
	print(image_list) 
	return(image_list)

#Takes a list as an input and returns a list of every nth item for n = SKIP
def Decimate_Index(LIST, SKIP):
	list_in = LIST
	print("DECIMATING")
	list_out = [list_in[i] for i in xrange(0, len(list_in), SKIP)]
	return(list_out)

#Applies colortable of corresponding wlen to black and white JP2 images.
def Colorize(FILE, SCALE = False, SCALEX = 0, SCALEY = 0):
	
	sorted_number = sorted_list.index(FILE)
	print("CONVERTING: " + str(FILE))
	convert_out = str(FILE).split(".")[0] + "-" + str(sorted_number) + ".png"
	subprocess.call("convert " + str(FILE) + " colortables/" + str(current_wavelength) + "_color_table.png -clut " + convert_out, shell = True)
	
	#ffmpeg blackmagic that alters the aspect ratio and adds padding as needed
	if(SCALE == True):
		subprocess.call('ffmpeg -i ' + str(convert_out) + ' -vf "scale=(iw*sar)*min(SCALEX/(iw*sar)\,' + SCALEY + '/ih):ih*min(' + SCALEX + '/(iw*sar)\,' + SCALEY + '/ih), pad=' + SCALEX + ':' + SCALEY + ':(' + SCALEX + '-iw*min(' + SCALEX + '/iw\,' + SCALEY + '/ih))/2:(' + SCALEY + '-ih*min(' + SCALEY + '/iw\,' + SCALEY + '/ih))/2"  -y ' + str(convert_out), shell = True)

	Annotate(convert_out)

#Takes an image file as input and annotates it with a selection of text. The text selection is currently hardcoded in, as it's more efficient to write multiple lines at once.
def Annotate(FILE):
	print("FILE: " + str(FILE))

	date = 0
	time = 0
	wlen = 0

	b,g,r,a = 191,191,191,0 #Text color

	print("ANNOTATING: " + str(FILE))

	#Parse data from filenames			
	date = str(FILE).split("__")[0].split("/")[1].replace("_", "-")
	time = str((FILE).split("__")[1])[:8].replace("_", ":")
	wlen = str(FILE).split(".")[0].split("__")[2].split("_")[3].split("-")[0]

	img = FILE
 
	img_pil = Image.open(FILE)
	if img_pil.mode != "RGB":
		img_pil = img_pil.convert("RGB")

	draw = ImageDraw.Draw(img_pil)

	draw.text((3700, 3705), "Observation Time:", font = ImageFont.truetype(fontpath, 56), fill = (b, g, r, a))
	draw.text((3700, 3785), str(date), font = font, fill = (b, g, r, a))
	draw.text((3700, 3855), str(time), font = font, fill = (b, g, r, a))
	draw.text((102, 3705), "Earth Added for Size Scale", font = ImageFont.truetype(fontpath, 56), fill = (b, g, r, a))
	#Turn it back in to a numpy array for OpenCV to deal with
	frameStamp = np.array(img_pil)
	annotate_out = "numbered/" + FILE.split("-")[1]

	cv2.imwrite(annotate_out, cv2.cvtColor(frameStamp, cv2.COLOR_RGB2BGR)) #It's critical to convert from BGR to RGB here, because OpenCV sees things differently from everyone else

#Adds an animated earth to the video, to scale
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

#Given a list arranged by AIA wavelength, returns a list sorted by temperature
def AIA_ArrangeByTemp(LIST):
	list_in = LIST
	list_order = [0, 5, 3 , 2, 1, 4]

	list_out = [list_in[i] for i in list_order]

	return(list_out)

#Generates background videos according to a template, for exhibits such as the NASM videowall
def Generate_Background(TEMPLATE, FEATURE, DURATION, VIDEONAME): #The template for video arrangement, EG: TEMPLATE_2x2.png

	im = ImageClip(TEMPLATE) 
	regions = findObjects(im)
	vlist = AIA_ArrangeByTemp(Video_List()) #Video_List() will sort by wavelength, but we want to sort by temperature
	print("vlist: " + str(vlist))
	clips = [VideoFileClip(n) for n in
		["misc/black.mp4",
		vlist[0],#The order they appear here is the order they appear on the Thermometer (?)
		vlist[1],
        vlist[2],
        vlist[3],
        vlist[4],
        vlist[5],
		FEATURE, #Second to last is our featured video
		"misc/black.mp4"]]

	comp_clips = [c.resize(r.size).set_mask(r.mask).set_pos(r.screenpos) for c,r in zip(clips,regions)] #We build our composite here.

	cc = CompositeVideoClip(comp_clips,im.size)

	cc.set_duration(DURATION).write_videofile(VIDEONAME, fps = 24, threads = 4, audio = False, progress_bar = True)

#Adds a graphical overlay to a video file. Designed to take the output from Generate_Background
def Add_Infographic(BASE, OVERLAY, OUTNAME): #BASE: Output of Generate_Background(), Overlay: the graphical overlay image EG: GENERIC_Wall_Base2x2.mp4, OVERLAY_2x2.png
	
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

	        cv2.imwrite("GENERIC_out" + str(i) + ".png", outImage)
	        i = i + 1
	
	        print("\rOverlaying frame: " + str(i), end = "")
	        stdout.flush() 

	        if cv2.waitKey(1) & 0xFF == ord('q'):
	            break
	    else:
	        break

	subprocess.call('ffmpeg -r 24 -i GENERIC_out%01d.png -vcodec libx264 -b:v 4M -pix_fmt yuv420p -y ' + str(OUTNAME), shell=True)

	for f in glob.glob("GENERIC_out*.png"):
	    os.remove(f)

	# Release everything if job is finished
	cap.release()

if __name__ == '__main__':
	try:	
		#Copy all the JP2s to a working directory so they aren't overwritten by checksdo.py while we're working on them
		for wlen in target_wavelengths: 
			if(os.path.isfile("live/" + wlen) == False):
				subprocess.call("mkdir -p live/", shell = True)
			
			for f in glob.glob("live/" + str(wlen) + "/*.jp2"): #get rid of jp2s from previous run
				os.remove(f)

			subprocess.call(['cp', '-r', wlen, "live/"]) #copy current JP2 list to a working directory
			print("COPYING: " + str(wlen))

		for wlen in target_wavelengths:

			sorted_list = Build_Index(str(wlen))
			sorted_list = Decimate_Index(sorted_list, 2)

			current_wavelength = wlen
			
			subprocess.call("rm " + str(wlen) + "/*.png", shell = True) #purge PNG files from previous runs. This is less than ideal, but neccessary until we solve the problem of shifting timeframes and corresponding frame numbers

			if os.path.isdir("numbered") == False:
				subprocess.call("mkdir numbered" , shell = True)
			else:
				for file in glob.glob("numbered/*.png"):
					os.remove(file)

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
		for n in range (0, 6):
			vlist = Video_List()
			vlist = AIA_ArrangeByTemp(vlist)
			feature = vlist[n]
			templateIn = "misc/TEMPLATE_2x3.png"
			videoOut = "working/NASM_Segment_" + str(n) + "_.mp4"
			
			print("Video In: " + feature + ", using template: " + templateIn)
			print("Segment Length: " + str(segment_length))
			
			AIA_GenerateBackground(templateIn, feature, segment_length, videoOut)

			baseVideoIn = "working/NASM_Segment_" + str(n) + "_.mp4"
			segmentVideoOut = "working/NASM_SegmentOverlay_" + str(n) + "_.mp4"
			overlayIn = "misc/OVERLAY_2x3_WHITE_" + str(n) + ".png"
			AIA_AddInfographic(baseVideoIn, overlayIn, segmentVideoOut)

			subprocess.call('killall ffmpeg', shell = True) #This is a temporary fix for the leaky way that Moviepy calls ffmpeg


		# Take all the clips we've generated, and stitch them in to one long video.
		clip1 = VideoFileClip("working/NASM_SegmentOverlay_0_.mp4")
		clip2 = VideoFileClip("working/NASM_SegmentOverlay_1_.mp4")
		clip3 = VideoFileClip("working/NASM_SegmentOverlay_2_.mp4")
		clip4 = VideoFileClip("working/NASM_SegmentOverlay_3_.mp4")
		clip5 = VideoFileClip("working/NASM_SegmentOverlay_4_.mp4")
		clip6 = VideoFileClip("working/NASM_SegmentOverlay_5_.mp4")

		final_outname = str(year) + "_" + str(month) + "_" + str(day) + "_GENERIC_VideoWall_DAILY.mp4"
		final_clip = concatenate_videoclips([clip6, clip5.crossfadein(1), clip4.crossfadein(1), clip3.crossfadein(1), clip2.crossfadein(1), clip1.crossfadein(1)], padding = -1, method = "compose")
		final_clip.write_videofile("daily_mov/" + str(final_outname), fps = 24, threads = 4, audio = False, progress_bar = True)

		subprocess.call("ffmpeg -i " + final_outname + " -filter:v scale=3840:-1 -c:a copy _" + final_outname, shell = True)
		os.rename(("_" + final_outname), final_outname)

		#SendText.Send_Text(str(final_outname) + " render complete! ")

	except:
		outname = year + month + day + "_GENERIC_VideoWall_DAILY.mp4"
		e = traceback.format_exc()
		#SendText.Send_Text("ERROR: failed to render custom video: " + str(outname) + "\n \n" + str(e))


