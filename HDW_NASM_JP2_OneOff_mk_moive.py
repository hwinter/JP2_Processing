from __future__ import print_function

import subprocess
import glob
import os
import datetime
import sys
import shutil
from multiprocessing import Pool

def internal_copy_files(file):
	new_name=os.path.join(out_folder, file.split("-")[1])
	if not os.path.isfile(new_name):
		#print("Copying "+file+" to "+new_name)
		shutil.copy2(file, new_name )
		
in_folder="continuum_2"
out_folder="numbered_2"
outname="test2.mp4"



#print("Combining frames into a movie")
#subprocess.call("ffmpeg -r 50 -i "+out_folder+"/%01d.png -vcodec libx264 -b:v 4M -pix_fmt yuv420p -crf 18 -y " +out_folder+"/"+outname, shell = True)
#subprocess.call('ffmpeg -i ' +out_folder+"/"+outname + ' -vf "scale=(iw*sar)*min(1200/(iw*sar)\,1200/ih):ih*min(1200/(iw*sar)\,1200/ih), pad=1200:1200:(1200-iw*min(1200/iw\,1200/ih))/2:(1200-ih*min(1200/iw\,1200/ih))/2" '+out_folder+'/SCALED_' + str(outname), shell = True)
#stop_val

if not os.path.isdir(out_folder):
	os.makedirs(out_folder)
#Identify PNG files
files=sorted(glob.glob(in_folder + "/*.png"))
#cp png files into a numbered list
print("Copying files")
pool = Pool()
pool.map(internal_copy_files, files)
pool.close()
pool.join()

#for file in files:
#	new_name=os.path.join(out_folder, file.split("-")[1])
#	if not os.path.isfile(new_name):
#		print("Copying "+file+" to "+new_name)
#		shutil.copy2(file, new_name )
	
#send that numbered list to ffmpeg to make a movie.

print("Combining frames into a movie")
subprocess.call("ffmpeg -r 50 -i "+out_folder+"/%01d.png -vcodec libx264 -b:v 4M -pix_fmt yuv420p -crf 18 -y " +out_folder+"/"+outname, shell = True)
subprocess.call('ffmpeg -i ' +out_folder+"/"+outname + ' -vf "scale=(iw*sar)*min(1200/(iw*sar)\,1200/ih):ih*min(1200/(iw*sar)\,1200/ih), pad=1200:1200:(1200-iw*min(1200/iw\,1200/ih))/2:(1200-ih*min(1200/iw\,1200/ih))/2" '+out_folder+'/SCALED_' + str(outname), shell = True)