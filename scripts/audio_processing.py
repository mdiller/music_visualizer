import librosa
import numpy as np
import inspect
from typing import get_type_hints
import hashlib
import os
from collections import OrderedDict

from data_classes import SpectrogramInfo


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
	def exists(self):
		return os.path.exists(self.filepath)

	@property
	def hash(self):
		if not self._hash:
			self._hash = hash_string(self.filepath)
		return self._hash

	def save(self, data: np.ndarray):
		self.data = data
		np.save(self.filepath, self.data)

	def read(self) -> np.ndarray:
		if self.data is None:
			self.data = np.load(self.filepath)
		return self.data
	
	def __repr__(self):
		return self.hash


class SongProcessor():
	info: SpectrogramInfo
	def __init__(self, name, filename, out_dir):
		self.name = name
		self.filename = filename
		self.out_dir = out_dir
		self.info_file = os.path.join(out_dir, "info.json")
		self.info = None
		self.print_lines = []
		if not os.path.exists(self.out_dir):
			os.makedirs(self.out_dir)

	def STEP_raw_spectrogram(
		self,
		midi_min: int = 9,
		framerate: int = 30,
		bins_per_octave: int = 48,
		octaves: int = 9
	) -> np.ndarray:
		data, sr = librosa.load(self.filename)
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

		return data
		# WRITE SOME MORE INFO GATHERING HERE FOR LOWER BOUNDS ETC, OR JUST HAVE THAT ON THE SIDE
	
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
		self.info.file_spectrogram = os.path.relpath(os.path.abspath(final_file.filepath), ROOT_DIR)

		return data

	def print(self, text):
		self.print_lines.append(text)
		if self.direct_print:
			print(text)

	def run(self, direct_print = False):
		self.direct_print = direct_print
		run_all = False
		if os.path.exists(self.info_file):
			self.info = SpectrogramInfo.fromFile(self.info_file)
		else:
			self.info = SpectrogramInfo()
			run_all = True
		
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
				filename = f"{func_name}_{input_hash}.npy"
				filename = os.path.join(self.out_dir, filename)
				step_output = StepOutput(filename)

				if (not step_output.exists) or run_all:
					self.print(f"Running: {func_name}{input_str}")
					result = func(**{k: v for k, v in arg_values.items() if v is not inspect.Parameter.empty})
					step_output.save(result)
				else:
					self.print(f"Verified: {func_name}.{input_hash}")
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