from __future__ import print_function

import matplotlib
matplotlib.use('agg')

from moviepy.editor import *
from moviepy.video.tools.segmenting import findObjects
from PIL import ImageFont, ImageDraw, Image
from astropy.io import fits
from sys import stdout as stdout
from numba import jit
from multiprocessing import Pool

# import aia_mkmovie as mm
import numpy as np
import sunpy.instr.aia as aia
import matplotlib.pyplot as plt

import cv2
import subprocess
import glob
import os
import datetime
import sys

import SendText
# import NASM_JP2_OneOff as cg


clips = []
seg_len = 0

for f in glob.glob("working/*.mp4"):
	clip = VideoFileClip(f).set_duration(24)
	print(f, "DURATION: ", clip.duration)
	clips.append(clip)

print("CLIPS: ", clips)
seg_len = clips[0].duration / len(clips)

for f in clips:
	
	print("F:", f, "SEG LEN: ", seg_len, "TIMES: ", str(clips.index(f) * seg_len), " - ", str((clips.index(f) * seg_len) + seg_len))
	clips[clips.index(f)] = f.subclip((clips.index(f) * seg_len),((clips.index(f) * seg_len) + seg_len))

final_clip = concatenate_videoclips([clips[0], clips[1].crossfadein(1), clips[2].crossfadein(1)], padding = -1, method = "compose")
final_clip.write_videofile("working/QTFL_TEST.mp4", fps = 24)