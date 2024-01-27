import os
import librosa
import numpy as np


from utils.keyfinder import Tonal_Fragment
from utils.data_cache import NumpyCache
from utils.data_classes import SongInfo, StemInfo
from utils.smart_stepper import DataStub, SmartStepper


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))

class SongProcessor(SmartStepper):
	info: SongInfo
	
	def __init__(self, song_name: str):
		song_dir = os.path.join(ROOT_DIR, "data", "songs", song_name)
		filename = os.path.join(song_dir, "song.mp3")
		super().__init__(f"Song - {song_name}", os.path.join(song_dir, "data", "_main"), SongInfo)
		self.name = song_name
		self.filename = filename
		
	def STEP_extract_audio(
		self,
	):
		data, sr = librosa.load(self.filename)
		
		self.info.name = self.name
		self.info.samplerate = sr
		self.info.duration = librosa.get_duration(y=data, sr=sr)

		return data

	def STEP_beat_timing(
		self,
		STEP_extract_audio: NumpyCache,
	):
		data = STEP_extract_audio.read()
		sr = self.info.samplerate

		onset_env = librosa.onset.onset_strength(y=data, sr=sr, aggregate=np.median)
		tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)

		beat_times = librosa.frames_to_time(beats, sr=sr)
		beat_time_diffs = np.zeros_like(beat_times)
		beat_time_diffs[0] = beat_times[0]
		for i in range(1, beat_times.shape[0]):
			beat_time_diffs[i] = beat_times[i] - beat_times[i - 1]

		self.info.bpm = tempo
		self.info.bpm_offset = beat_times[0]

		return DataStub(beat_time_diffs, 60)
	
	def STEP_key_finder(
		self,
		STEP_extract_audio: NumpyCache,
	):
		data = STEP_extract_audio.read()
		sr = self.info.samplerate

		y_harmonic, y_percussive = librosa.effects.hpss(data)

		key_finder = Tonal_Fragment(y_harmonic, sr)
		self.info.key = key_finder.get_key()

		