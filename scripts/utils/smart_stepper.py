
from collections import OrderedDict
import inspect
import os
import numpy as np

from utils.data_cache import NumpyCache, hash_string
from utils.data_classes import NumpyData


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", ".."))


class DataStub():
	def __init__(self, data: np.ndarray, framerate: float, offset: float = 0):
		self.data = data
		self.framerate = framerate
		self.offset = offset

class SmartStepper():
	def __init__(self, name: str, out_dir: str, info_type: type):
		self.processor_name = name
		self.out_dir = out_dir
		self.info_type = info_type
		self.info_file = os.path.join(out_dir, "info.json")
		if not os.path.exists(self.out_dir):
			os.makedirs(self.out_dir)
		self.info = None
		self.print_lines = []
	
	def run(self, direct_print = True):
		self.direct_print = direct_print
		run_all = False
		self.info = self.info_type()

		if direct_print:
			self.print(f"==> Processor: {self.processor_name}", 0)
		
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
					if param_type is NumpyCache:
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
				step_output = NumpyCache(filename)

				if (not step_output.exists) or run_all:
					self.print(f"Running: {func_name}{input_str}")
					json_before = self.info.toJson()
					result = func(**{k: v for k, v in arg_values.items() if v is not inspect.Parameter.empty})
					
					if isinstance(result, DataStub):
						result: DataStub
						# VERIFY KEY HERE
						# CREATE NEW CLASS HERE
						data_key = func_name.replace("STEP_", "DATA_")
						if not hasattr(self.info, data_key):
							raise Exception(f"MISSING KEY '{data_key}' IN '{self.info_type}'")
						
						data_thing = NumpyData()
						data_thing.filename = os.path.relpath(os.path.abspath(step_output.filepath_npy), ROOT_DIR)
						data_thing.framerate = result.framerate
						data_thing.offset = result.offset
						setattr(self.info, data_key, data_thing)

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
			for line in self.print_lines:
				print(line)
		
		return self.info
		# output_type = get_type_hints(func).get('return')
		# is_ndarray = output_type is np.ndarray

	def print(self, text: str, indent: int = 1):
		if indent > 0:
			text = f"  {text}"
		self.print_lines.append(text)
		if self.direct_print:
			print(text)