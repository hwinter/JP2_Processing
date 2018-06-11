import sys
import subprocess
import os

runs = int(raw_input("#RUNS: "))
wlen = []
year = []
month = []
day = []
timelapse = str(input("TIMELAPSE: "))
paragraph = []


for run in range(0,runs):
	wlen.append(str(input(str(run) + " WAVELENGTH: ")))
	year.append(str(input(str(run) + " YEAR: ")).zfill(4))
	month.append(str(input(str(run) + " MONTH: ")).zfill(2))
	day.append(str(input(str(run) + " DAY: ")).zfill(2))
	print("BODY (ctrl-D to end): ")

	#Take input for descriptive text
	lines = []
	while(True):
		new_line = raw_input()
		lines.append(str(new_line))
		if(new_line == ""):
			break
	paragraph.append(lines)
	# print(paragraph)

for run in range(0,runs):
	# print("RUN: " + str(run))
	body = """"""
	for i in paragraph[run]:
		# print("i: " + str(i))
		# print(paragraph[run].index(i))
		body = body + str(i) + "\n"
		# print(body)

	subprocess.call("printf '" + str(wlen[run]) + "\n" + str(year[run]) + "\n" + str(month[run]) + "\n" + str(day[run]) + "\n" + str(body) + str(timelapse) + "\n' | python test_NASM_jpeg2000_processing_.py", shell = True)
	# print("source activate AIADev && printf '" + str(wlen[run]) + "\n" + str(year[run]) + "\n" + str(month[run]) + "\n" + str(day[run]) + "\n" + str(body) + str(timelapse) + "\n' | python test_NASM_jpeg2000_processing_.py")