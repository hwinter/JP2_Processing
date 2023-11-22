import os
#os.chdir('/home/tracy/programs/git_folder/JP2_Processing-master')
from bs4 import BeautifulSoup
from time import sleep
import datetime

from JP2_Production import get_jp2_datetime

import requests
import subprocess
import glob


#import SendText

verbose =1 


year = "2023"
month = "09"
day = "29"
spectrum = ""
remove_old_files=1
n_days=2

target_wavelengths = ["94", "171", "193", "211", "304", "335"]
#target_wavelengths = ["193"]

#set to None for today's date
#time=None
time=time = datetime.now()-datetime.timedelta(days=n_days)


#target_wavelengths = ["335"]
url = "https://helioviewer.org/jp2/AIA/"  #EX: https://helioviewer.org/jp2/AIA/   ---   2018/09/24/94/
ext = 'jp2'

alist = []
lena = [0, 0, 0, 0, 0, 0]
lenb = [0, 0, 0, 0, 0, 0]

def build_helioviewer_URL(time=None):
	#Build a helioviewer url based on the given time
	if not time: time = datetime.datetime.now()
	time_str = str(time).split(" ")[0].split("-")
	year = time_str[0]
	month = time_str[1]
	day = time_str[2]
	urlout = url + str(year) + "/" + str(month) + "/" + str(day) + "/" 
	return(urlout)


def listFD(url, ext=''):
	#Go to url and find all of the files with the given extension
    page = requests.get(url).text
    # print page
    soup = BeautifulSoup(page, 'html.parser')
    return [url + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(ext)]

def Prune(folder, age=1, ext="jp2"):
	for file in glob.glob(folder + "/*."+ext):
		#file_mod_time = datetime.fromtimestamp(os.stat(file).st_mtime)
		file_DT, junk = get_jp2_datetime(file)
		if datetime.datetime.now() - file_DT >= datetime.timedelta(days=age): #
			if verbose >= 1: print("PRUNING: " + str(file))
			os.remove(file)

def check_SDO(URL, time=None, prune=None, n_days=2):
	#while True:

		if not time: time = datetime.datetime.now()
		# time = str(time).split(" ")[0].split("-")
		# urlout = URL + str(year) + "/" + str(month) + "/" + str(day) + "/" 
		urlout=build_helioviewer_URL(time)
		for wlen in target_wavelengths:

			url = urlout + str(wlen) + "/"
			windex = target_wavelengths.index(wlen)
			if verbose >= 1: print("CHECKING: " + str(url))
			lena[windex] = lenb[windex]
			alist = []
			for file in listFD(url, ext):
			    alist.append(str(file))

			print("LENGTH: " + str(len(alist)))
			#if(len(alist) == 0):
			#	SendText.Send_Text(str(datetime.datetime.now()) + "CHECKSDO ERROR: " + str(wlen) + " data not found." )
			
			lenb[windex] = len(alist)

			if((lenb[windex] - lena[windex]) < 0):
				lena[windex] = 0

			new = lenb[windex] - lena[windex] #Without the above if statement, When the day changes over, this becomes negative!!
			if verbose >= 1: print("NEW: " + str(new))
			if(new > 0):
				for file in range((lenb[windex] - new), lenb[windex]):
					if verbose >= 1: check = str(wlen) + "/" + str(alist[file]).split("//")[2]
					print("CHECK: " + check)
					if(os.path.isfile(str(wlen) + "/" + str(alist[file]).split("//")[2]) == False): #Don't download files you already have
						if verbose >= 1: print("CHECK: " + check)
						subprocess.call("wget -P " + str(wlen) + " " + str(alist[file]), shell = True)
			#Prune old files if there are new files
			if prune :
				folder = str(wlen) + "/"
				Prune(folder, age=n_days)


		#check every 15 minutes
	#	if verbose >= 1: print("Sleeping")

	#	sleep(900)

if __name__ == '__main__':
	time= datetime.datetime.now()-datetime.timedelta(days=5)
	check_SDO(url, time=time, prune=None, n_days=n_days)
