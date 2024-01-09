import librosa
import numpy as np
import inspect
from typing import get_type_hints
import hashlib
import os
from collections import OrderedDict
import json

from data_classes import StemInfo


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))

def hash_string(input: str):
	return hashlib.sha256(input.encode()).hexdigest()[:10]

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
		return data
	
	def STEP_volume(
		self,
		STEP_extract_audio: StepOutput,
		volume_framerate: int = 1
	):
		data = STEP_extract_audio.read()
		sr = 22050 # TODO: fix/update so that we can get this dynamically. librosa.get_samplerate gets wrong value. 

		# Calculate frame length and hop length
		frame_length = sr // volume_framerate
		hop_length = frame_length // 2  # 50% overlap

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

		return data, "DATA_volume"
	
	def STEP_volume_velocity(
		self,
		STEP_volume: StepOutput
	):
		data = STEP_volume.read()

		modifier = 1
		data = np.diff(data) / modifier

		return data, "DATA_volume_velocity"
	
	def STEP_volume_rolling_average(
		self,
		STEP_volume: StepOutput
	):
		data = STEP_volume.read()

		window_size = 3

		data = np.convolve(data, np.ones(window_size), 'valid') / window_size
		data /= np.max(data)

		return data, "DATA_volume_rolling_average"

	
	def STEP_raw_spectrogram(
		self,
		STEP_extract_audio: StepOutput,
		midi_min: int = 9,
		framerate: int = 30,
		bins_per_octave: int = 48,
		octaves: int = 9
	) -> np.ndarray:
		data = STEP_extract_audio.read()
		sr = 22050 # TODO: fix/update so that we can get this dynamically. librosa.get_samplerate gets wrong value. 
		fmin = librosa.midi_to_hz(midi_min)

		n_bins = octaves * bins_per_octave
		hop_length = int(sr / framerate)
		actual_framerate = sr / hop_length

		data = librosa.cqt(
			data,
			sr=sr,
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
	
	def STEP_decay_and_filter(
		self,
		STEP_normalize: StepOutput,
		decay_factor: float = 0.9,
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

		return data, "DATA_spectrogram"
	
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
		final_info_json = OrderedDict({})
		
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
					self.info = StemInfo()
					result = func(**{k: v for k, v in arg_values.items() if v is not inspect.Parameter.empty})
					info_json = self.info.toJson()
					
					if isinstance(result, tuple):
						result, info_key = result
						info_json[info_key] = os.path.relpath(os.path.abspath(step_output.filepath_npy), ROOT_DIR)

					step_output.save(result, info_json)
				else:
					self.print(f"Verified: {func_name}.{input_hash}")
					info_json = step_output.read_info()
				
				# apply our info changes if there were any
				for key in info_json:
					if info_json.get(key) is not None:
						final_info_json[key] = info_json[key]

				step_outputs[func_name] = step_output
				
				del unresolved_steps[func_name]
				stuff_done = True
		
		if unresolved_steps:
			self.print(f"ERROR: UNRESOLVED FUNCS AFTER RUNNING")
			raise Exception("ahhhh unresolved funcs")
		
		final_info = StemInfo.fromJson(final_info_json)
		final_info.writeFile(self.info_file)

		if not direct_print:
			print(self.name)
			for line in self.print_lines:
				print(line)
		# output_type = get_type_hints(func).get('return')
		# is_ndarray = output_type is np.ndarray