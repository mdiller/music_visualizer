import os
import subprocess
import typing
import librosa
import numpy as np
from collections import OrderedDict
import time
from joblib import Parallel, delayed
from data_classes import *
import json

# TODO: implement a script to download the song and place it in the folder as full_song.mp3

# PREREQUISITES FOR RUNNING THIS SCRIPT:
# - have a folder at songs/{song_name} which has in it at least song.mp3

# python -m spleeter separate -p spleeter:4stems -o output what_if.mp3

overwrite_stems = False
stems_model = "4stems" 
song_name = "dont_lose_sight"

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
SPLEETER_DIR = os.path.join(ROOT_DIR, "scripts/_spleeter")
SONG_DIR = os.path.join(ROOT_DIR, "songs", song_name)
song_mp3_filename = os.path.join(SONG_DIR, "song.mp3")
song_info_file = os.path.join(SONG_DIR, "song_info.json")

# STEP 1: SPLIT SONG INTO PARTS IF NOT ALREADY DONE

if not os.path.exists(song_mp3_filename):
	print(f"Can't find song mp3 file at: {song_mp3_filename}")
	exit(1)


stems_dir = os.path.join(SONG_DIR, "stems", stems_model)

if not os.path.exists(stems_dir):
	print("] Generating stems...")
	os.makedirs(stems_dir)
	if not os.path.exists(SPLEETER_DIR):
		os.makedirs(SPLEETER_DIR)

	command = f"python -m spleeter separate -p spleeter:{stems_model} -o \"{stems_dir}\" \"{song_mp3_filename}\""
	print(f"> {command}")
	subprocess.run(command, shell=True, check=True, cwd=SPLEETER_DIR)

stems_out_dir = os.path.join(stems_dir, "song")
spectrograms_raw_dir = os.path.join(SONG_DIR, "spectrograms_raw")
spectrograms_dir = os.path.join(SONG_DIR, "spectrograms")

class AudioData():
	def __init__(self, data: np.ndarray, sr: float):
		self.data = data
		self.sr = sr

FULL_SONG_STEMNAME = "song"
class SongStem():
	name: str
	audio_data: AudioData
	def __init__(self, name):
		self.name = name
		self.audio_data = None
	
	def load_audio(self):
		if not self.audio_data:
			print(f"] Loading audio for '{self.name}'...")
			data, sr = librosa.load(self.audio_file)
			self.audio_data = AudioData(data, sr) 
		return self.audio_data
	
	@property
	def audio_file(self):
		if self.name == FULL_SONG_STEMNAME:
			return song_mp3_filename
		else:
			return os.path.join(stems_out_dir, f"{self.name}.wav")
	
	@property
	def spectrogram_info_file(self):
		return os.path.join(spectrograms_raw_dir, f"{self.name}.json")
	
	@property
	def spectrogram_raw_file(self):
		return os.path.join(spectrograms_raw_dir, f"{self.name}.npy")
	
	@property
	def spectrogram_file(self):
		return os.path.join(spectrograms_dir, f"{self.name}.npy")

stems: typing.List[SongStem]
stems = []
for root, dirs, files in os.walk(stems_out_dir):
	for file in files:
		stems.append(SongStem(os.path.splitext(file)[0]))
stems.append(SongStem(FULL_SONG_STEMNAME))



# STEP 2: GENERATE RAW SPECTROGRAMS

# TODO: regenerate this data only if spectrogram config changes (will have to save a global config somewhere)
raw_spectrogram_config = OrderedDict([
	("fmin", librosa.midi_to_hz(9)),
	("framerate", 30),
	("bins_per_octave", 48),
	("octaves", 9)
])

if not os.path.exists(spectrograms_raw_dir):
	os.makedirs(spectrograms_raw_dir)

spectrogram_infos: typing.List[SpectrogramInfo]
spectrogram_infos = []

# TODO: make this async?
print("] Generating raw spectrograms...")
for stem in stems:
	if not os.path.exists(stem.spectrogram_raw_file):
		audio_data = stem.load_audio()
		print(f"] Generating raw spectrogram for '{stem.name}'")

		n_bins = raw_spectrogram_config["octaves"] * raw_spectrogram_config["bins_per_octave"]
		hop_length = int(audio_data.sr / raw_spectrogram_config["framerate"])
		actual_framerate = audio_data.sr / hop_length

		spectrogram = librosa.cqt(
			audio_data.data,
			sr=audio_data.sr,
			fmin=raw_spectrogram_config["fmin"],
			n_bins=n_bins,
			bins_per_octave=raw_spectrogram_config["bins_per_octave"],
			hop_length=hop_length)
		
		specinfo = SpectrogramInfo(
			name=stem.name,
			frame_count=spectrogram.shape[1],
			framerate=actual_framerate,
			octaves=raw_spectrogram_config["octaves"],
			bins_per_octave=raw_spectrogram_config["bins_per_octave"]
		)
		spectrogram_infos.append(specinfo)
		specinfo.writeFile(stem.spectrogram_info_file)
		
		np.save(stem.spectrogram_raw_file, spectrogram)
	else:
		spectrogram_infos.append(SpectrogramInfo.fromFile(stem.spectrogram_info_file))

# STEP 3: GENERATE PROCESSED SPECTROGRAMS

# TODO: regenerate this data only if spectrogram config changes (will have to save raw_spectrogram_config somewhere) (also have an option to only process 1 stem?)
final_spectrogram_config = OrderedDict([
	("amplitude_ref", 0.6),
	("decay_factor", 0.70),
	("remove_negatives", True),
	("fill_value_range", True)
])

if not os.path.exists(spectrograms_dir):
	os.makedirs(spectrograms_dir)

def process_spectrogram(stem: SongStem):
	data = np.load(stem.spectrogram_raw_file)

	data = librosa.amplitude_to_db(np.abs(data), ref=final_spectrogram_config["amplitude_ref"])
	data = librosa.util.normalize(data)

	decay_factor = final_spectrogram_config["decay_factor"]  # Adjust this value as needed
	# Iterate through the frames (columns in C)
	for i in range(1, data.shape[1]):
		for j in range(data.shape[0]):
			# Apply decay if the current value is lower than the decayed previous value
			data[j, i] = max(data[j, i], data[j, i-1] * decay_factor)

	data = data.T
	
	if final_spectrogram_config["remove_negatives"]:
		data = np.maximum(data, 0)
	# data += np.min(data)
	if final_spectrogram_config["fill_value_range"]:
		data /= np.max(data)


	
	# Convert to boolean: True for non-zero, False for zero
	non_zero = data > 0
	# Find the first non-zero index in each row for lower bounds
	lower_bounds = np.argmax(non_zero, axis=1)
	# Reverse each row, find the first non-zero index, and adjust the position for the upper bounds
	upper_bounds = data.shape[1] - np.argmax(non_zero[:, ::-1], axis=1) - 1
	# Adjust upper bounds in case the entire row is zeros
	upper_bounds = np.where(np.any(non_zero, axis=1), upper_bounds, -1)

	for info in spectrogram_infos:
		if info.name == stem.name:
			info.min_x = lower_bounds
			info.max_x = upper_bounds
			info.writeFile(stem.spectrogram_info_file)

	np.save(stem.spectrogram_file, data)



print("] Processing spectrograms...")

# TODO: formalize this asyncronous stuff a bit more, and split up the individual operations as well for each spectrogram
# TODO: splitting up the operations will involve caching the data after each step based on the input data + config params
# TODO: first step for the above is to implement the more advanced config, so we can do diffs on it
# - ideally eventually we have some sort of gui for editing this config
# - then a button on the gui to regenerate, and a terminal showing the regeneration process
# update: ok we made the class generator now just gotta use it
Parallel(n_jobs=len(stems))(delayed(process_spectrogram)(stem) for stem in stems if True)  # replace with your condition		



song_info = SongInfo()

song_info.spectrograms = spectrogram_infos

song_info.writeFile(song_info_file)

