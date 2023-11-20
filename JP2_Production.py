# -*- coding: utf-8 -*-
#JP2_Production.py
#REQUIREMENTS
#1. ffmpeg
#2. ImageMagick

#To Do
# 1. Need to add functions to check that necessary folders exist, and if the do not, create them.
# 2. Create a directory tree map 

#Not necessary after the introduction of Python 3 to general use. 
#from __future__ import print_function

import matplotlib
matplotlib.use('agg')

from moviepy.editor import *
#If moviepy is hinky try 
#pip uninstall moviepy  
#pip uninstall decorator
#pip install moviepy
#from https://github.com/Zulko/moviepy/issues/1986
from moviepy.video.tools.segmenting import findObjects
from PIL import ImageFont, ImageDraw, Image
# from astropy.io import image
from sys import stdout as stdout
from numba import jit
import multiprocessing as mp
#import multiprocess as mp 
from natsort import natsorted
import numpy as np
#sunpy.instr has been depreciated and replaced with Sunkit-instruments and aiapy
#However this is no longer necessary for JP2 processing.
#import sunpy.instr.aia as aia
#import aiapy as aia
#
# No longer necessary
# import matplotlib.pyplot as plt

import cv2
import subprocess
import glob
import os
import shutil
import datetime
import sys
import requests
import traceback


#import SendText

#Switches
#verbose = 1 for error checking, else =0
verbose = 1

#Set to 1 to use Multiproccessor or 0 to colorize frames in series
multiprocess=1

#Number of images to skip when making frames:
skip_frames=5
#skip_frames=100

earth2scale=-1

nasm_overlay=-1

fade_duration=1.0


#Set date and time globally
global_date = datetime.datetime.now()
global_date = str(global_date)
year = global_date.split("-")[0]
month = global_date.split("-")[1]
day = str(int(global_date.split("-")[2].split(" ")[0]) - 1).zfill(2)

#Set fonts for display
fontpath = "misc/BebasNeue-Regular.ttf"
font = ImageFont.truetype(fontpath, 56)

#Wavelengths that will be used in the display
target_wavelengths = ["94", "171", "193", "211", "304", "335"]
#target_wavelengths = ["171"]

temperatures_celsius = ["6,000,000 degrees Celsius", "1,000,000 degrees Celsius", "1,222,200 degrees Celsius", "2,000,000 degrees Celsius", "100,000 degrees Celsius", "2,500,000 degrees Celsius"]
temperatures_Fahrenheit = ["10,800,000 Degrees Fahrenheit", "4,500,000 Degrees Fahrenheit", "3,600,000 Degrees Fahrenheit", 
						   "2,200,000 Degrees Fahrenheit", "1,800,000 Degrees Fahrenheit", "180,000 Degrees Fahrenheit" ]
#Number of CPUs to use to make images and movies.  Set to -1 or 1 to use one thread at a time.
n_cpus=int(mp.cpu_count()/2)
#n_cpus=int(np.rint(n_cpus/2))
#n_cpus=-1

#Functions. Yes I am a functional programmer using Python! Come at me bro.

def Get_wave_from_filename(File_in):
	split_1=(File_in).split("_AIA_AIA_")
	split_2=split_1[1].split('-')
	wlen=int(split_2[0])
	return wlen

#Compiles a sorted list of JP2 files in a given directory
def Build_Index(DIR):
	image_list = []
	count = 0
	for image_file in sorted(glob.glob(DIR + "/*.jp2")):
		if verbose >=1 : print("\r Adding file: " + str(image_file) + " Entries: " + str(count), end = " ")
		image_list.append(str(image_file))
		count = count + 1
	if verbose >=1 : print(image_list) 
	return(image_list)

#Add the index number after the name of the file 
def Add_sort_num(FILES):
	ii=0
	new_files=[]

	for file in FILES:
		new_file=str(file).split(".")[0] + "--" + str(ii) + ".jp2"
		if verbose >=1 : 
			print(file +"->"+new_file)
		new_files.append(new_file)
		os.rename(file,new_file)
		ii+=1

	return new_files


#Takes a list as an input and returns a list of every nth item for n = SKIP
#Yes, I know that Decimate means reduced to a tenth.  Sue me.
def Decimate_Index(LIST, SKIP):
	list_in = LIST
	if verbose >=1 : print("DECIMATING")
	list_out = [list_in[i] for i in range(0, len(list_in), SKIP)]

	return(list_out)

#Applies colortable of corresponding wlen to black and white JP2 images.
def Colorize(FILE_in, SCALE = False, SCALEX = 0, SCALEY = 0,):
	if type(FILE_in) == list : 
		if verbose >=1 : 
			print("List in Annotation")
			print(File_In)
		FILE_in=FILE_in[0]

	if verbose >=1 : print("FILE_in= "+FILE_in)
	
	if verbose >=1 : print("FILE "+FILE_in+" in sorted list.")
		
	if verbose >=1 : print("CONVERTING: " + str(FILE_in))
		
	sorted_number =str(str(FILE_in).split("--")[1]).split(".")[0]

	if verbose >=1 : print("sorted_number= "+str(sorted_number))

	convert_out = str(FILE_in).split(".")[0] + ".png"
	if verbose >=1 : print("convert_out = "+convert_out)
	#convert_out=FILE
	if 'wlen' in globals(): 
		if verbose >=1 :
			print("wlen ok")
		wlen=Get_wave_from_filename(FILE_in)
		if verbose >=1 : print("wlen= "+str(wlen))

	else : 
		if verbose >=1 :print("wlen NOT ok")
		wlen=Get_wave_from_filename(FILE_in)
		if verbose >=1 : print("wlen= "+str(wlen))
	convert_call="convert " + str(FILE_in) + " colortables/" + str(wlen) + "_color_table.png -clut " + convert_out
	if verbose >=1 : print("Call to convert: "+convert_call)
	subprocess.call(convert_call, shell = True)

	#ffmpeg blackmagic that alters the aspect ratio and adds padding as needed
	if(SCALE == True):
		if verbose >=1 : print("SCALE function called")
		subprocess.call('ffmpeg -i ' + str(convert_out) + ' -vf "scale=(iw*sar)*min(SCALEX/(iw*sar)\,' + SCALEY + '/ih):ih*min(' + SCALEX + '/(iw*sar)\,' + SCALEY + '/ih), pad=' + SCALEX + ':' + SCALEY + ':(' + SCALEX + '-iw*min(' + SCALEX + '/iw\,' + SCALEY + '/ih))/2:(' + SCALEY + '-ih*min(' + SCALEY + '/iw\,' + SCALEY + '/ih))/2"  -y ' + str(convert_out), shell = True)
	if verbose >=1 : print("Start Annotation")
	if os.path.isfile(convert_out):
		Annotate(convert_out)
	else:
		print("Annotation failed. ", convert_out, "is not a file")
	if verbose >=1 : print("End Annotation")
	if verbose >=1 : print("End Colorize")

#Added a "caller" function to try to get native Python multiprocessing to work in interactive mode in iPython."
def Call_Colorize(FILES, no_of_cpus=None):
	if no_of_cpus == None : no_of_cpus=1
	# Using multiprocess.pool() to parallelize our frame rendering
	start = datetime.datetime.now()

	if verbose >=1 : print("Made it to Call_Colorize")
	if verbose >=1 : print("Number of files= "+str(len(FILES)))

	if no_of_cpus > 1:
		pool = mp.Pool(no_of_cpus)
		pool.map(Colorize, FILES)
		pool.close()
		pool.join()
	else:
		if verbose >=1 : print("Colorizing frame by frame")

		for frame_file in FILES:
			if verbose >=1 : print(frame_file)
			Colorize(frame_file)
	if verbose >=1 : print("Successfully completed Call_Colorize")


#Takes an image file as input and annotates it with a selection of text. The text selection is currently hardcoded in, as it's more efficient to write multiple lines at once.
def Annotate(File_In):
	if type(File_In) == list : 
		if verbose >=1 : 
			print("List in Annotation")
			print(File_In)
		File_In=File_In[0]
	if verbose >=1 : 
		print("Annotate")
		print("File_In: " + str(File_In))

	date_and_time_string=get_jp2_datetime(File_In)[1]
	date=date_and_time_string[0]
	time=date_and_time_string[1]
	b,g,r,a = 191,191,191,0 #Text color

	if verbose >=1 : print("ANNOTATING: " + str(File_In))

	#Parse data from filenames			
	#date = str(File_In).split("__")[0].split("/")[1].replace("_", "-")
	#time = str((File_In).split("__")[1])[:8].replace("_", ":")

	wlen = str(File_In).split(".")[0].split("__")[2].split("_")[3].split("-")[0]
	if verbose >=1 : 
		print("date: " + date)
		print("time: " + time)
		print("wavelength: " + wlen)
	
	
	if verbose >=1 : print("Opening image in pil")
	img_pil = Image.open(File_In)
	if img_pil.mode != "RGB":
		if verbose >=1 : print("Converting to RGB")
		img_pil = img_pil.convert("RGB")

	if verbose >=1 : print("creating draw object")
	draw = ImageDraw.Draw(img_pil)

	draw.text((3500, 3705), "Observation Time:", font = ImageFont.truetype(fontpath, 90), fill = (b, g, r, a))
	#draw.text((3700, 3785), str(date), font = font, fill = (b, g, r, a))
	#draw.text((3700, 3855), str(time), font = font, fill = (b, g, r, a))
	draw.text((3500, 3785), date_and_time_string[0], font = font, fill = (b, g, r, a))
	draw.text((3500, 3855), date_and_time_string[1], font = font, fill = (b, g, r, a))
	if verbose >=1 : print("applying timestamp... ")
	draw.text((102, 3705), "Temperature:", font = ImageFont.truetype(fontpath, 90), fill = (b, g, r, a))
	draw.text((102, 3785), temperatures_celsius[target_wavelengths.index(wlen)], font = font, fill = (b, g, r, a))
	draw.text((102, 3850), "Wavelength:", font = ImageFont.truetype(fontpath, 90), fill = (b, g, r, a))
	draw.text((102,3930), str(wlen)+' Angstroms', font = font, fill = (b, g, r, a))

	annotate_out = "numbered/" + File_In.split("--")[1]
	
	if verbose >=1 : print("annotate_out: " + annotate_out)
	#img_pil.save(File_In)
	img_pil.save(annotate_out)

	#draw.text((102, 3705), "Earth Added for Size Scale", font = ImageFont.truetype(fontpath, 56), fill = (b, g, r, a))

	#text_clip = TextClip(txt="Welcome to Guatapé, Colombia!".upper(),
    #                 size=(.8*image_clip.size[0], 0),
    #                 font=fontpath,
    #                 color="White")
	#Turn it back in to a numpy array for OpenCV to deal with
	#frameStamp = np.array(img_pil)

	#cv2.imwrite(annotate_out, cv2.cvtColor(frameStamp, cv2.COLOR_RGB2BGR)) #It's critical to convert from BGR to RGB here, because OpenCV sees things differently from everyone else
	if verbose >=1 : 
		print("completed cv2")
		print("Completed Annotation. Original FILE= "+ File_In)
		print("Completed Annotated FILE= "+ annotate_out)
	
	return annotate_out




#Adds an animated earth to the video, to scale
def Add_Earth(FILE):
	if verbose >=1 : print("ADDING EARTH TO: " + str(FILE))
	main_video = [VideoFileClip(FILE)]
	mainvideo_length = main_video[0].duration
	if verbose >=1 : print("MAIN LENGTH: ", str(mainvideo_length))

	mlength = mainvideo_length

	earth_g = VideoFileClip("misc/Earth_WhiteBox_TBG.gif", has_mask = True, fps_source = "fps") #It's important to specify the FPS source here because otherwise Moviepy for some reason assumes it's not 24 fps, which skews our speed calculations later on.

	earthvideo_length = 60 #I'm having a problem with Moviepy (go figure) skipping to what seems to be an arbitrary frame at the very end of the video, rather than looping seemlessly. It also does not accurately measure the duration of the gif.
	if verbose >=1 : print("EARTH LENGTH: ", str(earthvideo_length))

	speedmult = (earthvideo_length / mainvideo_length) #our Earth gif completes a full rotation in 60 seconds (to be completely accurate, it's 59.97. framerates). Here we're figuring out how much slower or faster the video needs to be to align our Earth rotation speed with the speed of our timelapse.
	if verbose >=1 : print("SPEEDMULT: ", str(speedmult))

	earth_g = earth_g.set_duration(earthvideo_length).fl_time(lambda t: speedmult*t).set_pos((102, 3635), relative = False).resize(0.07163) # to account for the downsized resolution of our template video. Current Earth size = 320 pixels
	if verbose >=1 : print("earth_g")
	#The above statement is the meat and potatos of this script.
	#SPEED: We use fl_time to match the rotational speed of earth to our timelapse. where t = realtime speed of the video, we multiply t by the ratio of our Earth gif's length (1 min) to our main video length, assuming that our main video is a 24 hour timelapse of varying speed.
	#SET POSITION: We use set_position() to position the Earth, using relative percentages of overall screen size. EG: 0.85, 0.85 means 85% of the way across the screen along the x and y axes.
	#RESIZE: resize() resizes our Earth gif by a percentage, in this case derived by Earth's diameter in pixels (407 in our Whiteboxed example) divided by the sun's (3178 at native AIA resolution). 
	#set_position() and resize() both accept lambda t: values, so our Earth gif can be resized and moved dynamically.

	main_video.extend( [earth_g] )
	if verbose >=1 : print("main_video")
	out_video = CompositeVideoClip(main_video)
	if verbose >=1 : print("out_video")
	if verbose >=1 : print(str(FILE).split(".")[0] + "_.mp4")
	out_video_name=str(FILE).split(".")[0] + "_.mp4"
	if verbose >=1 : print("out_video_name: "+out_video_name)
	if mlength is None:
		if verbose >=1 : print("mlength was None")
		mlength = mainvideo_length
		if verbose >=1 : print("now mlength = "+str(mlength))
	else:
		if verbose >=1 : print("mlength: "+str(mlength))
	
	#breakpoint()
	#out_video.set_duration(mlength).write_videofile(out_video_name, fps = 24, threads = 2, audio = False, progress_bar = True)
	#out_video.set_duration(mlength).write_videofile(out_video_name, fps = 24, threads = 2, audio = False)
	if verbose >=1 : print("After out_video out_video_name: "+out_video_name)
	if verbose >=1 : print("After out_video FILE: "+FILE)
	
	#os.rename(out_video_name, FILE)
	if verbose >=1 : print("Add_Earth File: " + FILE)

##FROM AIA
#Returns a lis of .mp4 videos in the working/wav_vids
def Video_List():
	if verbose >=1 : print("Video_List")
	videolist = []
	for f in sorted(glob.glob("working/wav_vids/*.mp4")):
		videolist.append(str(f))

	return videolist

#Given a list arranged by AIA wavelength, returns a list sorted by temperature
def AIA_ArrangeByTemp(LIST):
	list_in = LIST
	list_order = [0, 5, 3 , 2, 1, 4]

	list_out = [list_in[i] for i in list_order]

	return list_out 

#Generates background videos according to a template, for exhibits such as the NASM videowall
#depreciated
def Generate_Background(TEMPLATE, FEATURE, DURATION, VIDEONAME): #The template for video arrangement, EG: TEMPLATE_2x2.png

	im = ImageClip(TEMPLATE) 
	regions = findObjects(im)
	vlist = AIA_ArrangeByTemp(Video_List()) #Video_List() will sort by wavelength, but we want to sort by temperature
	if verbose >=1 : print("vlist: " + str(vlist))
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

def Combine_clips(vlist):
		
		clip1 = VideoFileClip(str(vlist[0]))
		clip2 = VideoFileClip(str(vlist[1]))
		clip3 = VideoFileClip(str(vlist[2]))
		clip4 = VideoFileClip(str(vlist[3]))
		clip5 = VideoFileClip(str(vlist[4]))
		clip6 = VideoFileClip(str(vlist[5]))

		final_outname = str(year) + "_" + str(month) + "_" + str(day) + "_GENERIC_VideoWall_DAILY.mp4"
		if verbose >=1 : print(final_outname)

		final_clip = concatenate_videoclips([clip6, clip5.crossfadein(1), clip4.crossfadein(1), clip3.crossfadein(1), clip2.crossfadein(1), clip1.crossfadein(1)], padding = -1, method = "compose")
		final_clip.write_videofile("daily_mov/" + str(final_outname), fps = 24, threads = 4, audio = False)#, progress_bar = True)
		shutil.copy2("daily_mov/" + str(final_outname),("daily_mov/Daily_movie.mp4" ))
		return final_clip

def Add_overlay():
	return 0

	''
def get_jp2_datetime(filename):
	
	if os.path.isfile(filename):
		base_name=os.path.basename(filename).split(".")[0]
		date = str(base_name).split("__")[0].replace("_", "-")
		time = str((base_name).split("__")[1])[:8].replace("_", ":")+'.'+str((base_name).split("__")[1])[9:]

		date_string_dict=[date,time]
		format_string= "%Y-%m-%d %H:%M:%S.%f"
		date_and_time = datetime.datetime.strptime(date+' '+time, format_string)
	else:
		print("No file named "+filename)
		date_and_time=-1
		date_string_dict=["Error", "No file named "+filename]
		
	return date_and_time, date_string_dict

if __name__ == '__main__':
	start_0 = datetime.datetime.now()
	if verbose >=1 : print("Target wavelengths= ",target_wavelengths)
	try:	
		#Copy all the JP2s to a working directory so they aren't overwritten by checksdo.py while we're working on them
		for wlen in target_wavelengths: 
			if verbose >=1 : print("On wavelength "+ str(target_wavelengths.index(wlen)) + " of "+str(len(target_wavelengths)))
			if(os.path.isfile("live/" + str(wlen)) == False):
				subprocess.call("mkdir -p live/" + str(wlen), shell = True)
			
			
			if verbose >=1 : print("Starting glob #1")
			for f in glob.glob("live/" + str(wlen) + "/*.jp2"): #get rid of jp2s from previous run
				if verbose >=1 : print("Removing file "+f)
				os.remove(f)
			if verbose >=1 : print("Starting glob #2")
			for f in glob.glob("live/" + str(wlen) + "/*.png"): #get rid of png files from previous run
				if verbose >=1 : print("Removing file "+f)
				os.remove(f)

			#if verbose >=1 : print("Copying to live directory")
			#subprocess.call(['cp', '-r', wlen, "live/"]) #copy current JP2 list to a working directory
			#if verbose >=1 : print("COPYING: " + str(wlen))
		
		for wlen in target_wavelengths:
			if verbose >=1 : print("Current Wavelength: "+ str(wlen))
			sorted_list = Build_Index(str(wlen))
			if skip_frames >=1:
				sorted_list = Decimate_Index(sorted_list, skip_frames)

			for sorted_file in sorted_list:
				new_path="live/"+str(wlen)+"/"
				if verbose >=1 : print(sorted_file+" " +new_path)
				shutil.copy2(sorted_file,new_path)
			sorted_list = Build_Index("live/"+str(wlen))
			sorted_list=Add_sort_num(sorted_list)

			
			subprocess.call("rm " + str(wlen) + "/*.png", shell = True) #purge PNG files from previous runs. This is less than ideal, but neccessary until we solve the problem of shifting timeframes and corresponding frame numbers

			if os.path.isdir("numbered") == False:
				subprocess.call("mkdir numbered" , shell = True)
			else:
				for file in glob.glob("numbered/*.png"):
					os.remove(file)
			if verbose >=1 : 
				for sorted_list_file in sorted_list:
					print('Filenames to Call_Colorize= '+sorted_list_file)
			if verbose >=1 : print("Starting colorization")

			if verbose >= 1 : start = datetime.datetime.now()
			Call_Colorize(sorted_list, no_of_cpus=n_cpus)
			
			if verbose >= 1 : 
				finish = datetime.datetime.now()
				frame_timer = finish - start
				print("Frame colorize time: " + str(frame_timer))
			

			if verbose >= 1 : print("Creating movie from frames")
			png_sorted_list= natsorted(glob.glob("numbered/*.png"))
			video=ImageSequenceClip(png_sorted_list, fps=24)
			video=video.resize([1330,1330])
			#subprocess.call("ffmpeg -r 24 -i numbered/%01d.png -vcodec libx264 -b:v 4M -pix_fmt yuv420p -crf 18 -y "+wlen_file_temp, shell = True)
			wlen_file="working/wav_vids/" + str(wlen).zfill(4) + ".mp4"
			if os.path.isfile(wlen_file) : os.remove(wlen_file)
			#subprocess.call("ffmpeg -y -i "+wlen_file_temp+" -i misc/Overlay.png -filter_complex [0]overlay=x=0:y=0[out] -map [out] -map 0:a? "+wlen_file, shell = True)
			#subprocess.call("ffmpeg -i "+wlen_file_temp+" -vf scale=1330:1330 "+wlen_file, shell = True)
			#video = VideoFileClip(wlen_file)
			if verbose >= 1 : print("Adding overlay")
			title= ImageClip("misc/Overlay.png").set_start(0).set_duration(video.duration).set_pos(("center","center"))
			final = CompositeVideoClip([video, title])
			final.write_videofile(wlen_file)
			if verbose >= 1 : print("Finished final.write (Overlay) "+wlen_file)
			
			"""
			if earth2scale >= 1:
				Add_Earth("working/wav_vids/" + str(wlen).zfill(4) + ".mp4")
				if verbose >= 1 : print("Completed Add_Earth "+"working/wav_vids/" + str(wlen).zfill(4) + ".mp4")
			"""
			"""
			The range of the CRF scale is 0–51, where 0 is lossless, 23 is the default, and 51 is worst quality possible. 
			A lower value generally leads to higher quality, and a subjectively sane range is 17–28. 
			Consider 17 or 18 to be visually lossless or nearly so; it should look the same or nearly the same as the input but it isn't technically lossless.
			"""
			
			Add_overlay()

			if verbose >=1 :
				print("Successfully made "+str(wlen)+"video.")
				print("Deleting jp2 files in live/"+str(wlen))
			for f in glob.glob("live/" + str(wlen) + "/*.jp2"): #get rid of jp2s from previous run
				if verbose >=1 : print("Removing file "+f)
				os.remove(f)
			if verbose >=1 : print("Deleted jp2 files in live/"+str(wlen))
			finish = datetime.datetime.now()

			render_timer = finish - start_0
			if verbose >=1 : 
				print("TOTAL FRAMES: " + str(len(sorted_list)))
				print("PROCESSING TIME: " + str(frame_timer))
				print("RENDERING TIME: " + str(render_timer))
				print("here 2")

			for png_file in sorted_list:
				subprocess.call("rm " +png_file, shell = True) #purge files when done to save on disk space.  

		if verbose >= 1 : print("Combining clips")		
		vlist = Video_List()
		if verbose >=1 : print("vlist= ", vlist)
		vlist = AIA_ArrangeByTemp(vlist)
		if verbose >=1 : print("vlist= ", vlist)

		# Take all the clips we've generated, and stitch them in to one long video.
		Combine_clips(vlist)
		
		#final_outname = "daily_mov/" + str(year) + "_" + str(month) + "_" + str(day) + "_GENERIC_VideoWall_DAILY.mp4"
		#subprocess.call("ffmpeg -i " + final_outname + " -filter:v scale=3840:-1 -c:a copy _" + final_outname, shell = True)
		#os.rename(("_" + final_outname), final_outname)

		#SendText.Send_Text(str(final_outname) + " render complete! ")
		if verbose >=1 : print("Successful Completion")
	except:
	#	outname = year + month + day + "_GENERIC_VideoWall_DAILY.mp4"
		e = traceback.format_exc()
		if verbose >=1 : print("Failure")
		#SendText.Send_Text("ERROR: failed to render custom video: " + str(outname) + "\n \n" + str(e))
	
