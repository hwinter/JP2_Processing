import subprocess
import glob
import os

def Purge_Media():
	target_wavelengths = ["94", "171", "193", "211", "304", "335", "continuum", "magnetogram"]

	for wlen in target_wavelengths:

		print("PURGING: " + str(wlen))
		
		for f in glob.glob(str(wlen) + "/*.png"):
			    os.remove(f)
		for f in glob.glob(str(wlen) + "/*.jp2*"):
			    os.remove(f)

if __name__ == "__main__":
	Purge_Media()
