from bs4 import BeautifulSoup
from time import sleep
import requests

url = "http://jsoc.stanford.edu/data/aia/images/2018/04/10/335/"
ext = 'jp2'

alist = []
blist = []
lena = 0
lenb = 0

def listFD(url, ext=''):
    page = requests.get(url).text
    print page
    soup = BeautifulSoup(page, 'html.parser')
    return [url + '/' + node.get('href') for node in soup.find_all('a') if node.get('href').endswith(ext)]


while True:
	lena = lenb
	alist = []
	for file in listFD(url, ext):
	    alist.append(str(file))

	print("LENGTH: " + str(len(alist)))
	lenb = len(alist)
	print("NEW: " + str(lenb - lena))
	sleep(60)