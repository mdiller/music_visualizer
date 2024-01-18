import os
import subprocess
import typing
import librosa
import numpy as np
from collections import OrderedDict
import time
from joblib import Parallel, delayed
import json

import schema
schema.regenerate_schema() # only regenerates if there are changes

from data_classes import *
from audio_processing import SongProcessor
from process_poses import process_videos

# TODO: implement a script to download the song and place it in the folder as full_song.mp3

# PREREQUISITES FOR RUNNING THIS SCRIPT:
# - have a folder at songs/{song_name} which has in it at least song.mp3


# python -m spleeter separate -p spleeter:4stems -o output what_if.mp3

overwrite_stems = False
stems_model = "4stems" 
song_name = "im_insecure"

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
SPLEETER_DIR = os.path.join(ROOT_DIR, "scripts/_spleeter")
SONG_DIR = os.path.join(ROOT_DIR, "songs", song_name)
song_mp3_filename = os.path.join(SONG_DIR, "song.mp3")
song_info_file = os.path.join(SONG_DIR, "song_info.json")
GENERATED_DIR = os.path.join(ROOT_DIR, "src/generated/")
song_info_file2 = os.path.join(GENERATED_DIR, "song_info.json")
mp3_link_stub_file = os.path.join(GENERATED_DIR, "song_mp3.js")
VIDEOS_DIR = os.path.join(ROOT_DIR, "scripts", "videos")

# STEP 1: SPLIT SONG INTO PARTS IF NOT ALREADY DONE

if not os.path.exists(song_mp3_filename):
	print(f"Can't find song mp3 file at: {song_mp3_filename}")
	exit(1)


stems_dir = os.path.join(SONG_DIR, "stems", stems_model)

if (not os.path.exists(stems_dir)) or (not os.listdir(stems_dir)):
	print("] Generating stems...")
	if not os.path.exists(stems_dir):
		os.makedirs(stems_dir)
	if not os.path.exists(SPLEETER_DIR):
		os.makedirs(SPLEETER_DIR)

	command = f"python -m spleeter separate -p spleeter:{stems_model} -o \"{stems_dir}\" \"{song_mp3_filename}\""
	print(f"> {command}")
	subprocess.run(command, shell=True, check=True, cwd=SPLEETER_DIR)

stems_out_dir = os.path.join(stems_dir, "song")
spectrograms_raw_dir = os.path.join(SONG_DIR, "spectrograms_raw")
spectrograms_dir = os.path.join(SONG_DIR, "spectrograms")

FULL_SONG_STEMNAME = "song"
class SongStem():
	name: str
	def __init__(self, name):
		self.name = name
		self.processor = SongProcessor(
			self.name,
			self.audio_file,
			os.path.join(SONG_DIR, f"data/{name}"))
	
	@property
	def audio_file(self):
		if self.name == FULL_SONG_STEMNAME:
			return song_mp3_filename
		else:
			return os.path.join(stems_out_dir, f"{self.name}.wav")
	


stems: typing.List[SongStem]
stems = []
for root, dirs, files in os.walk(stems_out_dir):
	for file in files:
		stems.append(SongStem(os.path.splitext(file)[0]))
stems.append(SongStem(FULL_SONG_STEMNAME))

print("] Processing audio data...")

for stem in stems:
	print(f"==> {stem.name}:")
	stem.processor.run(True)

# def process_stem(stem: SongStem):
# 	stem.processor.run()
# Parallel(n_jobs=len(stems))(delayed(process_stem)(stem) for stem in stems)

stem_infos = []
for stem in stems:
	stem_infos.append(StemInfo.fromFile(stem.processor.info_file))

print("")

song_info = SongInfo()

song_info.poses = process_videos(SONG_DIR, VIDEOS_DIR, GENERATED_DIR)
song_info.stems = stem_infos

song_info.writeFile(song_info_file)
song_info.writeFile(song_info_file2)

with open(mp3_link_stub_file, "w+") as f:
	f.write(f"import audio from '../../songs/{song_name}/song.mp3'\nexport const MP3_FILE = audio;")

print("processing poses...")

print("done!")

# TODO: really gotta make a version of our spectrogram where notes that are held are super emphasized, or even a version that ONLY shows notes that are held
# TODO: also should maybe add a filter that only cares about differences/up/downs that last more than x miliseconds, which will let us pay attention more to just notes and less to noise?

# TODO: have an AVERAGE_FREQUENCY line that just gets the average frequency currently playing, weighing the ones higher that are playing with more volume, and as a companion to it, a thing that can tell us whether or not we're currently making sound

# TODO: next big step prolly after gradient is to make the py processing myuch more efficeint!