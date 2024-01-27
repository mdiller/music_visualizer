'''''
PROMPT:

[- Used So Far: 0.06319999999999999¢ | 471 tokens -]
'''''
import librosa
import numpy as np
import inspect
from typing import get_type_hints
import hashlib
import os
from collections import OrderedDict
import json
from utils.data_cache import NumpyCache, hash_string

import matplotlib

import utils.numpytools as numpytools
from utils.smart_stepper import DataStub, SmartStepper
matplotlib.use('Agg')

from utils.data_classes import NumpyData, SongInfo, StemInfo

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))

class StemProcesser(SmartStepper):
	info: StemInfo
	def __init__(self, stem_name: str, filename: str, song_info: SongInfo):
		self.song_info = song_info
		song_dir = os.path.join(ROOT_DIR, "data", "songs", song_info.name)
		super().__init__(f"Stem - {stem_name}", os.path.join(song_dir, "data", stem_name), StemInfo)
		self.name = stem_name
		self.filename = filename
		
	def STEP_extract_audio(
		self,
	):
		data, sr = librosa.load(self.filename)
		self.info.samplerate = sr
		return data
	
	def STEP_beats(
		self,
		STEP_extract_audio: NumpyCache,
	):
		# data, samplerate = librosa.load(librosa.ex('choice'), duration=10)
		data = STEP_extract_audio.read()
		# samplerate = self.info.samplerate
		# onset_env = librosa.onset.onset_strength(y=data, sr=samplerate, aggregate=np.median)
		# tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=samplerate)
		# # frames_time = librosa.frames_to_time(beats, sr=self.info.samplerate)
		# beat_bins = 5
		# beat_data = np.zeros(np.max(beats) + 1)
		# for i in range(beats.shape[0]):
		# 	beat_data[beats[i]] = 1

		# self.info.bpm = tempo
		# return DataStub(beat_data, "DATA_beats", 200)
		return data
	
	def STEP_volume(
		self,
		STEP_extract_audio: NumpyCache,
		overlap: int = 2,
	):
		bpm = self.song_info.bpm
		volume_framerate: float = 2 * bpm / 60
		data = STEP_extract_audio.read()

		# Calculate frame length and hop length
		# frame_length = self.info.samplerate // volume_framerate
		# hop_length = frame_length // 2  # 50% overlap

		hop_length = int(self.info.samplerate // volume_framerate)
		frame_length = hop_length * overlap

		# Compute short-term Fourier transform
		stft = librosa.stft(data, n_fft=frame_length, hop_length=hop_length)

		# Calculate  power spectrum
		powerSpectrum = np.abs(stft)**2

		# Compute RMS energy for each frame
		rms = librosa.feature.rms(S=powerSpectrum, frame_length=frame_length, hop_length=hop_length)

		# Flatten the array to get a 1D array representing volume over time
		data = rms.flatten()

		data = np.maximum(data, 0)
		data /= np.max(data)

		return DataStub(data, volume_framerate)
	
	def STEP_volume_velocity(
		self,
		STEP_volume: NumpyCache
	):
		data = STEP_volume.read()

		modifier = 1
		data = np.diff(data) / modifier

		return DataStub(data, self.info.DATA_volume.framerate)
	
	def STEP_volume_detailed_average(
		self,
		STEP_extract_audio: NumpyCache,
	):
		overlap = 2
		window_size = 10

		volume_framerate = self.info.framerate
		data = STEP_extract_audio.read()

		# Get volume data
		hop_length = int(self.info.samplerate // volume_framerate)
		frame_length = hop_length * overlap
		stft = librosa.stft(data, n_fft=frame_length, hop_length=hop_length)
		powerSpectrum = np.abs(stft)**2
		rms = librosa.feature.rms(S=powerSpectrum, frame_length=frame_length, hop_length=hop_length)
		data = rms.flatten()

		# Rolling average volume data
		data = np.convolve(data, np.ones(window_size), 'valid') / window_size

		data = np.maximum(data, 0)
		data /= np.max(data)

		return DataStub(data, volume_framerate)
	
	def STEP_volume_rolling_average(
		self,
		STEP_volume: NumpyCache
	):
		data = STEP_volume.read()

		window_size = 3

		data = np.convolve(data, np.ones(window_size), 'valid') / window_size
		data /= np.max(data)

		return DataStub(data, self.info.DATA_volume.framerate)

	
	def STEP_raw_spectrogram(
		self,
		STEP_extract_audio: NumpyCache,
		midi_min: int = 9,
		framerate: int = 30,
		bins_per_octave: int = 48,
		octaves: int = 9
	) -> np.ndarray:
		data = STEP_extract_audio.read()
		fmin = librosa.midi_to_hz(midi_min)

		n_bins = octaves * bins_per_octave
		hop_length = int(self.info.samplerate / framerate)
		actual_framerate = self.info.samplerate / hop_length

		data = librosa.cqt(
			data,
			sr=self.info.samplerate,
			fmin=fmin,
			n_bins=n_bins,
			bins_per_octave=bins_per_octave,
			hop_length=hop_length)
		
		self.info.name = self.name
		self.info.frame_count = data.shape[1]
		self.info.framerate = actual_framerate
		self.info.octaves = octaves
		self.info.bins_per_octave = bins_per_octave

		return data

	def STEP_normalize(
		self,
		STEP_raw_spectrogram: NumpyCache,
		amplitude_ref: float = 0.6
	) -> np.ndarray:
		data = STEP_raw_spectrogram.read() 

		data = librosa.amplitude_to_db(np.abs(data), ref=amplitude_ref)
		data = librosa.util.normalize(data)

		return data

	def STEP_spectrogram_held_notes(
		self,
		STEP_normalize: NumpyCache
	) -> np.ndarray:
		data = STEP_normalize.read()
		threshold = 0.3
		growth_rate = 1.0
		decay_rate = 10.0
		max_seconds = 1
		threshold_seconds = 0.2
		max_frames = self.info.framerate * max_seconds
		threshold_frames = threshold_seconds * self.info.framerate

		data = data.T
		result = np.copy(data)
		hold_duration = np.zeros(data.shape[1])
		for frame in reversed(range(data.shape[0])):
			for bin in range(data.shape[1]):
				if data[frame, bin] > threshold:
					if hold_duration[bin] < max_frames:
						hold_duration[bin] += growth_rate
				else:
					if hold_duration[bin] > 0:
						hold_duration[bin] -= np.minimum(decay_rate, hold_duration[bin])
				
				if hold_duration[bin] > threshold_frames:
					result[frame, bin] += hold_duration[bin]
				else:
					result[frame, bin] = 0
		
		result[0, 0] = 1
				
		result = np.maximum(result, 0)
		result /= np.max(result)

		return DataStub(result, self.info.framerate)

	def STEP_spectrogram(
		self,
		STEP_normalize: NumpyCache,
	) -> np.array:
		data = STEP_normalize.read()

		data = data.T
		
		data = np.maximum(data, 0)
		data /= np.max(data)

		return DataStub(data, self.info.framerate)

	
	def STEP_spectrogram_decayed(
		self,
		STEP_normalize: NumpyCache,
		decay_factor: float = 0.80, # default/good value is 0.8
		remove_negatives: bool = True,
		fill_value_range: bool = True
	) -> np.ndarray:
		data = STEP_normalize.read()

		if decay_factor > 0:
			# Iterate through the frames (columns in C)
			for i in range(1, data.shape[1]):
				for j in range(data.shape[0]):
					# Apply decay if the current value is lower than the decayed previous value
					data[j, i] = max(data[j, i], data[j, i-1] * decay_factor)

		data = data.T
		
		if remove_negatives:
			data = np.maximum(data, 0)
		# data += np.min(data)
		if fill_value_range:
			data /= np.max(data)

		return DataStub(data, self.info.framerate)
	
	def STEP_super_decay(
		self,
		STEP_normalize: NumpyCache,
	) -> np.ndarray:
		data = STEP_normalize.read()
		decay_factor = 0

		if decay_factor > 0:
			# Iterate   through the frames (columns in C)
			for i in range(1, data.shape[1]):
				for j in range(data.shape[0]):
					# Apply decay if the current value is lower than the decayed previous value
					data[j, i] = max(data[j, i], data[j, i-1] * decay_factor)

		data = data.T
		
		data = np.maximum(data, 0)
		data /= np.max(data)
		return data
		
	def STEP_peak_adjusted_spectrogram(
		self,
		STEP_super_decay: NumpyCache,
		STEP_spectrogram_decayed: NumpyCache
	) -> np.ndarray:
		super_data = STEP_super_decay.read()
		data = STEP_spectrogram_decayed.read()

		peak_data = np.amax(data, axis=1)

		# peak_data = self.rolling_average(peak_data, 80)

		peak_data = np.maximum(peak_data, 0.01)
		peak_data = np.reciprocal(peak_data)

		data *= peak_data[:, np.newaxis]

		data = numpytools.apply_decay(data, 0.7)

		data = numpytools.rolling_average2d(data, 10)

		data = np.maximum(data, 0)
		data /= np.max(data)
		return DataStub(data, self.info.framerate)

	
	
	def STEP_frequency_average(
		self,
		STEP_spectrogram_decayed: NumpyCache
	) -> np.ndarray:
		data = STEP_spectrogram_decayed.read()

		frequencies = np.zeros(data.shape[0])
		# Create an array of frequency indices (assuming they start from 0 and go up by 1)
		frequency_indices = np.arange(data.shape[1])


		for i in range(data.shape[0]):
			if np.sum(data[i]) != 0:
				frequencies[i] = np.average(frequency_indices, weights=data[i])
			# weighted_sum = np.sum(frequency_indices * data[i])
			# total_intensity = np.sum(data[i])
			# frequencies[i] = weighted_sum / total_intensity
		
		frequencies /= data.shape[1]

		return DataStub(frequencies, self.info.framerate)
	
	def STEP_final(
		self,
		STEP_spectrogram_decayed: NumpyCache,
		edge_cutoff: int = 0.1,
	) -> np.ndarray:
		final_file = STEP_spectrogram_decayed
		data = final_file.read() # test1

		lower_bounds = []
		upper_bounds = []
		for frame in data:
			non_zero_indices = np.where(frame > edge_cutoff)[0]
			if non_zero_indices.size > 0:
				lowest_x = np.min(non_zero_indices)
				highest_x = np.max(non_zero_indices)
				lower_bounds.append(lowest_x)
				upper_bounds.append(highest_x)
			# else:
			# 	lower_bounds.append(0)
			# 	upper_bounds.append(len(frame))

		self.info.min_x = int(np.min(lower_bounds))
		self.info.max_x = int(np.max(upper_bounds))
