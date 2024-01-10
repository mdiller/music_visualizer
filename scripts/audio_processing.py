import librosa
import numpy as np
import inspect
from typing import get_type_hints
import hashlib
import os
from collections import OrderedDict
import json
import matplotlib
matplotlib.use('Agg')

from data_classes import NumpyData, StemInfo


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))

def hash_string(input: str):
	return hashlib.sha256(input.encode()).hexdigest()[:10]

class DataStub():
	def __init__(self, data: np.ndarray, key: str, framerate: float, offset: float = 0):
		self.data = data
		self.key = key
		self.framerate = framerate
		self.offset = offset

class StepOutput():
	def __init__(self, filepath):
		self.filepath = filepath
		self.data = None
		self._hash = None
		self.direct_print = False
	
	@property
	def filepath_npy(self):
		return self.filepath + ".npy"

	@property
	def filepath_json(self):
		return self.filepath + ".json"
	
	@property
	def exists(self):
		return os.path.exists(self.filepath_json)

	@property
	def hash(self):
		if not self._hash:
			self._hash = hash_string(self.filepath)
		return self._hash

	def save(self, data: np.ndarray, info: OrderedDict):
		if data is None:
			data = np.empty([1, 1])
		self.data = data
		np.save(self.filepath_npy, self.data)
		text = json.dumps(info)
		with open(self.filepath_json, "w+") as f:
			f.write(text)

	def read(self) -> np.ndarray:
		if self.data is None:
			self.data = np.load(self.filepath_npy)
		return self.data
	
	def read_info(self) -> OrderedDict:
		with open(self.filepath_json, "r") as f:
			return json.loads(f.read(), object_pairs_hook=OrderedDict)
	
	def __repr__(self):
		return self.hash


class SongProcessor():
	info: StemInfo
	def __init__(self, name, filename, out_dir):
		self.name = name
		self.filename = filename
		self.out_dir = out_dir
		self.info_file = os.path.join(out_dir, "info.json")
		self.info = None
		self.print_lines = []
		if not os.path.exists(self.out_dir):
			os.makedirs(self.out_dir)
		
	def STEP_extract_audio(
		self,
	):
		data, sr = librosa.load(self.filename)
		self.info.samplerate = sr
		return data
	
	def STEP_beats(
		self,
		STEP_extract_audio: StepOutput,
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
		STEP_extract_audio: StepOutput,
		overlap: int = 2,
	):
		bpm = 67 # TODO: calculate this later
		volume_framerate: float = 2 * bpm / 60
		data = STEP_extract_audio.read()

		# Calculate frame length and hop length
		# frame_length = self.info.samplerate // volume_framerate
		# hop_length = frame_length // 2  # 50% overlap

		hop_length = int(self.info.samplerate // volume_framerate)
		frame_length = hop_length * overlap

		# Compute short-term Fourier transform
		stft = librosa.stft(data, n_fft=frame_length, hop_length=hop_length)

		# Calculate power spectrum
		powerSpectrum = np.abs(stft)**2

		# Compute RMS energy for each frame
		rms = librosa.feature.rms(S=powerSpectrum, frame_length=frame_length, hop_length=hop_length)

		# Flatten the array to get a 1D array representing volume over time
		data = rms.flatten()

		data = np.maximum(data, 0)
		data /= np.max(data)

		return DataStub(data, "DATA_volume", volume_framerate)
	
	def STEP_volume_velocity(
		self,
		STEP_volume: StepOutput
	):
		data = STEP_volume.read()

		modifier = 1
		data = np.diff(data) / modifier

		return DataStub(data, "DATA_volume_velocity", self.info.DATA_volume.framerate)
	
	def STEP_volume_rolling_average(
		self,
		STEP_volume: StepOutput
	):
		data = STEP_volume.read()

		window_size = 3

		data = np.convolve(data, np.ones(window_size), 'valid') / window_size
		data /= np.max(data)

		# can get the framerate for below by doing info.DATA_volume.framerate
		# SHOULD ALSO HAVE an offset parameter, sometimes we want to offset x time into the data before doing framerate?
		# should prolly have these be the same units actually.. ms?
		return DataStub(data, "DATA_volume_rolling_average", self.info.DATA_volume.framerate)

	
	def STEP_raw_spectrogram(
		self,
		STEP_extract_audio: StepOutput,
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
		STEP_raw_spectrogram: StepOutput,
		amplitude_ref: float = 0.6
	) -> np.ndarray:
		data = STEP_raw_spectrogram.read()

		data = librosa.amplitude_to_db(np.abs(data), ref=amplitude_ref)
		data = librosa.util.normalize(data)

		return data

	def STEP_spectrogram_held_notes(
		self,
		STEP_normalize: StepOutput
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

		return DataStub(result, "DATA_spectrogram_held_notes", self.info.framerate)

	def STEP_spectro_clean(
		self,
		STEP_normalize: StepOutput,
	) -> np.array:
		data = STEP_normalize.read()

		data = data.T
		
		data = np.maximum(data, 0)
		data /= np.max(data)

		return DataStub(data, "DATA_spectrogram", self.info.framerate)

	
	def STEP_decay_and_filter(
		self,
		STEP_normalize: StepOutput,
		decay_factor: float = 0.8,
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

		return DataStub(data, "DATA_spectrogram_decayed", self.info.framerate)
	
	def STEP_final(
		self,
		STEP_decay_and_filter: StepOutput,
		edge_cutoff: int = 0.1,
	) -> np.ndarray:
		final_file = STEP_decay_and_filter
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

	def print(self, text):
		self.print_lines.append(text)
		if self.direct_print:
			print(text)

	def run(self, direct_print = False):
		self.direct_print = direct_print
		run_all = False
		self.info = StemInfo()
		
		if run_all:
			self.print("Running all...")
		
		# get func list dir
		unresolved_steps = OrderedDict({})
		step_outputs = OrderedDict({})
		for func_name, func in inspect.getmembers(self, predicate=inspect.ismethod):
			if func_name.startswith("STEP_"):
				unresolved_steps[func_name] = func

		stuff_done = True
		while stuff_done:
			stuff_done = False
			func_names = list(unresolved_steps.keys())
			for func_name in func_names:
				func = unresolved_steps[func_name]
				sig = inspect.signature(func)
				arg_values = OrderedDict({})
				can_run = True
				for param in sig.parameters.values():
					param_type = param.annotation if param.annotation is not inspect.Parameter.empty else None
					value = param.default if param.default is not inspect.Parameter.empty else None
					if param_type is StepOutput:
						if param.name in step_outputs:
							value = step_outputs[param.name]
						else:
							can_run = False
							break # skip this if we dont have the input for it yet
					
					if value is None:
						self.print(f"ERROR: missing default value for {func_name}.{param.name}")
						raise Exception("ahhhh missing default value!")
					arg_values[param.name] = value
				if not can_run:
					continue

				input_str = "_".join(map(lambda arg: str(arg), arg_values.items()))
				input_str = f"[{hash_string(inspect.getsource(func))}]: {input_str}"
				input_hash = hash_string(input_str)
				filename = f"{func_name}_{input_hash}"
				filename = os.path.join(self.out_dir, filename)
				step_output = StepOutput(filename)

				if (not step_output.exists) or run_all:
					self.print(f"Running: {func_name}{input_str}")
					json_before = self.info.toJson()
					result = func(**{k: v for k, v in arg_values.items() if v is not inspect.Parameter.empty})
					
					if isinstance(result, DataStub):
						result: DataStub
						# VERIFY KEY HERE
						# CREATE NEW CLASS HERE
						if not hasattr(StemInfo(), result.key):
							raise Exception(f"MISSING KEY '{result.key}' IN StemInfo")
						
						data_thing = NumpyData()
						data_thing.filename = os.path.relpath(os.path.abspath(step_output.filepath_npy), ROOT_DIR)
						data_thing.framerate = result.framerate
						data_thing.offset = result.offset
						setattr(self.info, result.key, data_thing)

						result = result.data
						
					info_json = self.info.toJson()
					
					duplicate_keys = []
					for key in info_json:
						if json_before.get(key) == info_json.get(key):
							duplicate_keys.append(key)
					for key in duplicate_keys:
						del info_json[key]

					step_output.save(result, info_json)
				else:
					self.print(f"Verified: {func_name}.{input_hash}")
					info_json = step_output.read_info()
					self.info.updateFromJson(info_json)

				# apply our info changes if there were any

				step_outputs[func_name] = step_output
				
				del unresolved_steps[func_name]
				stuff_done = True
		
		if unresolved_steps:
			self.print(f"ERROR: UNRESOLVED FUNCS AFTER RUNNING")
			raise Exception("ahhhh unresolved funcs")
		
		self.info.writeFile(self.info_file)

		if not direct_print:
			print(self.name)
			for line in self.print_lines:
				print(line)
		# output_type = get_type_hints(func).get('return')
		# is_ndarray = output_type is np.ndarray