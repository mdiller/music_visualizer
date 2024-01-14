import os
import numpy as np
import hashlib
from collections import OrderedDict
import json

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))

def hash_string(input: str):
	return hashlib.sha256(input.encode()).hexdigest()[:10]

class NumpyCache():
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