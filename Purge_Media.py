import subprocess
import glob
import os

target_wavelengths = ["94", "171", "193", "211", "304", "335"]

for wlen in target_wavelengths:{
	
	for f in glob.glob(str(wlen) + "*.png"):
		    os.remove(f)
	for f in glob.glob(str(wlen) + "*.jp2"):
		    os.remove(f)
	for f in glob.glob(str(wlen) + "*.1"):
		    os.remove(f)	
}

