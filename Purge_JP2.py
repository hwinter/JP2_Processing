import glob
import os
import datetime
import sys

target_wavelengths = ["94", "171", "193", "211", "304", "335", "continuum", "magnetogram"]

for wlen in target_wavelengths:
	for file in glob.glob(str(wlen) + "/*.jp2*"):
		print("REMOVING: " + str(file))
		os.remove(file)