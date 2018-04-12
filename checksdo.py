from bs4 import BeautifulSoup
from time import sleep
from datetime import datetime, timedelta
import requests
import subprocess
import glob
import os

year = ""
month = ""
day = ""
spectrum = ""

target_wavelengths = ["94", "171", "193", "211", "304", "335"]

url = "http://jsoc.stanford.edu/data/aia/images/2018/04/10/335/"
ext = 'jp2'

alist = []
blist = []
lena = [0, 0, 0, 0, 0, 0]
lenb = [0, 0, 0, 0, 0, 0]



def buildURL():
	time = datetime.now()
	time = str(time).split(" ")[0].split("-")
	year = time[0]
	month = time[1]
	day = time[2]
	urlout = "http://jsoc.stanford.edu/data/aia/images/" + str(year) + "/" + str(month) + "/" + str(day) + "/" 
	return(urlout)

def listFD(url, ext=''):
    page = requests.get(url).text
    # print page
    soup = BeautifulSoup(page, 'html.parser')
    return [url + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(ext)]


while True:

	time = datetime.now()
	time = str(time).split(" ")[0].split("-")
	year = time[0]
	month = time[1]
	day = time[2]
	urlout = "http://jsoc.stanford.edu/data/aia/images/" + str(year) + "/" + str(month) + "/" + str(day) + "/" 

	for wlen in target_wavelengths:
		for file in glob.glob(str(wlen) + "/*.jp2"):
			file_mod_time = datetime.fromtimestamp(os.stat(file).st_mtime)
			if(int(str(datetime.today() - file_mod_time).split(":")[0]) > 24): #if a file is more than 24 hours old
				print("PRUNING: " + str(file))
				os.remove(file)

	for wlen in target_wavelengths:
		url = urlout + str(wlen) + "/"
		windex = target_wavelengths.index(wlen)
		print("CHECKING: " + str(url))
		lena[windex] = lenb[windex]
		alist = []
		for file in listFD(url, ext):
		    alist.append(str(file))

		print("LENGTH: " + str(len(alist)))
		lenb[windex] = len(alist)
		new = lenb[windex] - lena[windex]
		print("NEW: " + str(new))
		if(new > 0):
			for file in range((lenb[windex] - new), lenb[windex]):
				subprocess.call("wget -P " + str(wlen) + " " + str(alist[file]), shell = True)



	sleep(900)


