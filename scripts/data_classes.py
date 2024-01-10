# VERSION_HASH: 50dcde7c61_a5e676d4a9
import json
from collections import OrderedDict

class StemInfo():
	def __init__(self, name = None, samplerate = None, frame_count = None, framerate = None, octaves = None, bins_per_octave = None, min_x = None, max_x = None, bpm = None, bpm_offset = None, DATA_spectrogram = None, DATA_volume = None, DATA_volume_velocity = None, DATA_volume_rolling_average = None, DATA_spectrogram_held_notes = None, DATA_spectrogram_decayed = None, DATA_volume_in_time = None):
		self.name = name
		self.samplerate = samplerate
		self.frame_count = frame_count
		self.framerate = framerate
		self.octaves = octaves
		self.bins_per_octave = bins_per_octave
		self.min_x = min_x
		self.max_x = max_x
		self.bpm = bpm
		self.bpm_offset = bpm_offset
		self.DATA_spectrogram = DATA_spectrogram
		self.DATA_volume = DATA_volume
		self.DATA_volume_velocity = DATA_volume_velocity
		self.DATA_volume_rolling_average = DATA_volume_rolling_average
		self.DATA_spectrogram_held_notes = DATA_spectrogram_held_notes
		self.DATA_spectrogram_decayed = DATA_spectrogram_decayed
		self.DATA_volume_in_time = DATA_volume_in_time

	def toJson(self):
		return OrderedDict([
			("name", self.name),
			("samplerate", self.samplerate),
			("frame_count", self.frame_count),
			("framerate", self.framerate),
			("octaves", self.octaves),
			("bins_per_octave", self.bins_per_octave),
			("min_x", self.min_x),
			("max_x", self.max_x),
			("bpm", self.bpm),
			("bpm_offset", self.bpm_offset),
			("DATA_spectrogram", self.DATA_spectrogram if self.DATA_spectrogram is None else self.DATA_spectrogram.toJson()),
			("DATA_volume", self.DATA_volume if self.DATA_volume is None else self.DATA_volume.toJson()),
			("DATA_volume_velocity", self.DATA_volume_velocity if self.DATA_volume_velocity is None else self.DATA_volume_velocity.toJson()),
			("DATA_volume_rolling_average", self.DATA_volume_rolling_average if self.DATA_volume_rolling_average is None else self.DATA_volume_rolling_average.toJson()),
			("DATA_spectrogram_held_notes", self.DATA_spectrogram_held_notes if self.DATA_spectrogram_held_notes is None else self.DATA_spectrogram_held_notes.toJson()),
			("DATA_spectrogram_decayed", self.DATA_spectrogram_decayed if self.DATA_spectrogram_decayed is None else self.DATA_spectrogram_decayed.toJson()),
			("DATA_volume_in_time", self.DATA_volume_in_time if self.DATA_volume_in_time is None else self.DATA_volume_in_time.toJson()),
		])

	def updateFromJson(self, json: OrderedDict):
		if json is None:
			return
		if "name" in json:
			self.name = json.get("name")
		if "samplerate" in json:
			self.samplerate = json.get("samplerate")
		if "frame_count" in json:
			self.frame_count = json.get("frame_count")
		if "framerate" in json:
			self.framerate = json.get("framerate")
		if "octaves" in json:
			self.octaves = json.get("octaves")
		if "bins_per_octave" in json:
			self.bins_per_octave = json.get("bins_per_octave")
		if "min_x" in json:
			self.min_x = json.get("min_x")
		if "max_x" in json:
			self.max_x = json.get("max_x")
		if "bpm" in json:
			self.bpm = json.get("bpm")
		if "bpm_offset" in json:
			self.bpm_offset = json.get("bpm_offset")
		if "DATA_spectrogram" in json:
			self.DATA_spectrogram = NumpyData.fromJson(json.get("DATA_spectrogram"))
		if "DATA_volume" in json:
			self.DATA_volume = NumpyData.fromJson(json.get("DATA_volume"))
		if "DATA_volume_velocity" in json:
			self.DATA_volume_velocity = NumpyData.fromJson(json.get("DATA_volume_velocity"))
		if "DATA_volume_rolling_average" in json:
			self.DATA_volume_rolling_average = NumpyData.fromJson(json.get("DATA_volume_rolling_average"))
		if "DATA_spectrogram_held_notes" in json:
			self.DATA_spectrogram_held_notes = NumpyData.fromJson(json.get("DATA_spectrogram_held_notes"))
		if "DATA_spectrogram_decayed" in json:
			self.DATA_spectrogram_decayed = NumpyData.fromJson(json.get("DATA_spectrogram_decayed"))
		if "DATA_volume_in_time" in json:
			self.DATA_volume_in_time = NumpyData.fromJson(json.get("DATA_volume_in_time"))

	@classmethod
	def fromJson(cls, json: OrderedDict):
		self = StemInfo()
		self.updateFromJson(json)
		return self

	@classmethod
	def fromFile(cls, filename: str):
		with open(filename, "r") as f:
			return StemInfo.fromJson(json.loads(f.read()))

	def writeFile(self, filename: str):
		text = json.dumps(self.toJson(), indent="\t")
		with open(filename, "w+") as f:
			f.write(text)

class NumpyData():
	def __init__(self, filename = None, framerate = None, offset = None):
		self.filename = filename
		self.framerate = framerate
		self.offset = offset

	def toJson(self):
		return OrderedDict([
			("filename", self.filename),
			("framerate", self.framerate),
			("offset", self.offset),
		])

	def updateFromJson(self, json: OrderedDict):
		if json is None:
			return
		if "filename" in json:
			self.filename = json.get("filename")
		if "framerate" in json:
			self.framerate = json.get("framerate")
		if "offset" in json:
			self.offset = json.get("offset")

	@classmethod
	def fromJson(cls, json: OrderedDict):
		self = NumpyData()
		self.updateFromJson(json)
		return self

	@classmethod
	def fromFile(cls, filename: str):
		with open(filename, "r") as f:
			return NumpyData.fromJson(json.loads(f.read()))

	def writeFile(self, filename: str):
		text = json.dumps(self.toJson(), indent="\t")
		with open(filename, "w+") as f:
			f.write(text)

class SongInfo():
	def __init__(self, stems = None):
		self.stems = stems

	def toJson(self):
		return OrderedDict([
			("stems", list(map(lambda x: x if x is None else x.toJson(), self.stems))),
		])

	def updateFromJson(self, json: OrderedDict):
		if json is None:
			return
		if "stems" in json:
			self.stems = list(map(lambda x: StemInfo.fromJson(x), json.get("stems")))
			self.stems = json.get("stems")

	@classmethod
	def fromJson(cls, json: OrderedDict):
		self = SongInfo()
		self.updateFromJson(json)
		return self

	@classmethod
	def fromFile(cls, filename: str):
		with open(filename, "r") as f:
			return SongInfo.fromJson(json.loads(f.read()))

	def writeFile(self, filename: str):
		text = json.dumps(self.toJson(), indent="\t")
		with open(filename, "w+") as f:
			f.write(text)
