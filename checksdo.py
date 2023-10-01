from bs4 import BeautifulSoup
from time import sleep
from datetime import datetime, timedelta

import requests
import subprocess
import glob
import os

#import SendText

verbose =1 

#set to None for today's date
year = "2023"
month = "09"
day = "29"
spectrum = ""

target_wavelengths = ["94", "171", "193", "211", "304", "335"]

#target_wavelengths = ["335"]
url = "https://helioviewer.org/jp2/AIA/"  #EX: https://helioviewer.org/jp2/AIA/   ---   2018/09/24/94/
ext = 'jp2'

alist = []
lena = [0, 0, 0, 0, 0, 0]
lenb = [0, 0, 0, 0, 0, 0]



def buildURL():
	time = datetime.now()
	time = str(time).split(" ")[0].split("-")
	year = time[0]
	month = time[1]
	day = time[2]
	urlout = url + str(year) + "/" + str(month) + "/" + str(day) + "/" 
	return(urlout)

def listFD(url, ext=''):
    page = requests.get(url).text
    # print page
    soup = BeautifulSoup(page, 'html.parser')
    return [url + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(ext)]

def check_SDO(URL, year=year, month=month, day=day):
	while True:

		time = datetime.now()
		time = str(time).split(" ")[0].split("-")
		if not year: year = time[0]
		if not month: month = time[1]
		if not day: day = time[2]
		urlout = URL + str(year) + "/" + str(month) + "/" + str(day) + "/" 

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
			#	SendText.Send_Text(str(datetime.now()) + "CHECKSDO ERROR: " + str(wlen) + " data not found." )
			
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
			for file in glob.glob(str(wlen) + "/*.jp2"):
				file_mod_time = datetime.fromtimestamp(os.stat(file).st_mtime)
				if(str(datetime.now() - file_mod_time).find("day") != -1): #if a file is more than 24 hours old
					if verbose >= 1: print("PRUNING: " + str(file))
					os.remove(file)

		#check every 15 minutes
		if verbose >= 1: print("Sleeping")

		sleep(900)

if __name__ == '__main__':
	check_SDO(url, year=year, month=month, day=day)

