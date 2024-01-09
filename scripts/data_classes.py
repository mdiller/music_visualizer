# VERSION_HASH: 06fc4e7ebb_d66a70a9b0
import json
from collections import OrderedDict

class StemInfo():
	def __init__(self, name = None, frame_count = None, framerate = None, octaves = None, bins_per_octave = None, min_x = None, max_x = None, DATA_spectrogram = None, DATA_volume = None, DATA_volume_velocity = None, DATA_volume_rolling_average = None):
		self.name = name
		self.frame_count = frame_count
		self.framerate = framerate
		self.octaves = octaves
		self.bins_per_octave = bins_per_octave
		self.min_x = min_x
		self.max_x = max_x
		self.DATA_spectrogram = DATA_spectrogram
		self.DATA_volume = DATA_volume
		self.DATA_volume_velocity = DATA_volume_velocity
		self.DATA_volume_rolling_average = DATA_volume_rolling_average

	def toJson(self):
		return OrderedDict([
			("name", self.name),
			("frame_count", self.frame_count),
			("framerate", self.framerate),
			("octaves", self.octaves),
			("bins_per_octave", self.bins_per_octave),
			("min_x", self.min_x),
			("max_x", self.max_x),
			("DATA_spectrogram", self.DATA_spectrogram),
			("DATA_volume", self.DATA_volume),
			("DATA_volume_velocity", self.DATA_volume_velocity),
			("DATA_volume_rolling_average", self.DATA_volume_rolling_average),
		])

	@classmethod
	def fromJson(cls, json: OrderedDict):
		self = StemInfo()
		self.name = json.get("name")
		self.frame_count = json.get("frame_count")
		self.framerate = json.get("framerate")
		self.octaves = json.get("octaves")
		self.bins_per_octave = json.get("bins_per_octave")
		self.min_x = json.get("min_x")
		self.max_x = json.get("max_x")
		self.DATA_spectrogram = json.get("DATA_spectrogram")
		self.DATA_volume = json.get("DATA_volume")
		self.DATA_volume_velocity = json.get("DATA_volume_velocity")
		self.DATA_volume_rolling_average = json.get("DATA_volume_rolling_average")
		return self

	@classmethod
	def fromFile(cls, filename: str):
		with open(filename, "r") as f:
			return StemInfo.fromJson(json.loads(f.read()))

	def writeFile(self, filename: str):
		text = json.dumps(self.toJson(), indent="\t")
		with open(filename, "w+") as f:
			f.write(text)

class SongInfo():
	def __init__(self, stems = None):
		self.stems = stems

	def toJson(self):
		return OrderedDict([
			("stems", list(map(lambda x: x.toJson(), self.stems))),
		])

	@classmethod
	def fromJson(cls, json: OrderedDict):
		self = SongInfo()
		self.stems = list(map(lambda x: StemInfo.fromJson(x), json.get("stems")))
		return self

	@classmethod
	def fromFile(cls, filename: str):
		with open(filename, "r") as f:
			return SongInfo.fromJson(json.loads(f.read()))

	def writeFile(self, filename: str):
		text = json.dumps(self.toJson(), indent="\t")
		with open(filename, "w+") as f:
			f.write(text)
