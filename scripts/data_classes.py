import json
from collections import OrderedDict

class SpectrogramInfo():
	def __init__(self, name = None, frame_count = None, framerate = None, octaves = None, bins_per_octave = None, min_x = None, max_x = None):
		self.name = name
		self.frame_count = frame_count
		self.framerate = framerate
		self.octaves = octaves
		self.bins_per_octave = bins_per_octave
		self.min_x = min_x
		self.max_x = max_x

	def toJson(self):
		return OrderedDict([
			("name", self.name),
			("frame_count", self.frame_count),
			("framerate", self.framerate),
			("octaves", self.octaves),
			("bins_per_octave", self.bins_per_octave),
			("min_x", self.min_x),
			("max_x", self.max_x),
		])

	@classmethod
	def fromJson(cls, json: OrderedDict):
		self = SpectrogramInfo()
		self.name = json.get("name")
		self.frame_count = json.get("frame_count")
		self.framerate = json.get("framerate")
		self.octaves = json.get("octaves")
		self.bins_per_octave = json.get("bins_per_octave")
		self.min_x = json.get("min_x")
		self.max_x = json.get("max_x")
		return self

	@classmethod
	def fromFile(cls, filename: str):
		with open(filename, "r") as f:
			return SpectrogramInfo.fromJson(json.loads(f.read()))

	def writeFile(self, filename: str):
		with open(filename, "w+") as f:
			f.write(json.dumps(self.toJson(), indent="\t"))

class SongInfo():
	def __init__(self, spectrograms = None):
		self.spectrograms = spectrograms

	def toJson(self):
		return OrderedDict([
			("spectrograms", list(map(lambda x: x.toJson(), self.spectrograms))),
		])

	@classmethod
	def fromJson(cls, json: OrderedDict):
		self = SongInfo()
		self.spectrograms = list(map(lambda x: SpectrogramInfo.fromJson(x), json.get("spectrograms")))
		return self

	@classmethod
	def fromFile(cls, filename: str):
		with open(filename, "r") as f:
			return SongInfo.fromJson(json.loads(f.read()))

	def writeFile(self, filename: str):
		with open(filename, "w+") as f:
			f.write(json.dumps(self.toJson(), indent="\t"))
