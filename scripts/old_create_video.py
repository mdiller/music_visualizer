import numpy, scipy, matplotlib.pyplot as plt, IPython.display as ipd
import librosa, librosa.display
import os
from matplotlib.animation import FFMpegWriter
import subprocess
import shutil
from PIL import Image, ImageDraw
import colorsys

from pydub import AudioSegment, playback

def get_color(bin_num, bin_count):
	hue = bin_num / bin_count  # This will give a hue value in the range [0, 1]
	# Convert HSV to RGB (using full saturation and value)
	r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)
	# Convert RGB from [0, 1] range to [0, 255] range
	r, g, b = int(r * 255), int(g * 255), int(b * 255)
	return (r, g, b)

def make_freq_vid(input_file):
	rootfile, ext = os.path.splitext(input_file)

	output_file = rootfile + ".mp4"
	print("loading audio...")
	x, sr = librosa.load(input_file)
	ipd.Audio(x, rate=sr)

	fmin = librosa.midi_to_hz(9)
	framerate = 30
	bins_per_octave = 48
	octaves = 9
	n_bins = octaves * bins_per_octave
	hop_length = int(sr / framerate)

	# TODO: INVESTIGATE OTHER SPECTROGRAMS IN FUTURE
	# C = librosa.feature.melspectrogram(y=x, sr=sr, n_mels=128, fmax=8000, hop_length=hop_length)

	print("doin spectrogram...")
	C = librosa.cqt(x, sr=sr, fmin=fmin, n_bins=n_bins, bins_per_octave=bins_per_octave, hop_length=hop_length)
	# C = librosa.feature.chroma_cens(y=x, sr=sr, hop_length=hop_length)

	C = librosa.amplitude_to_db(numpy.abs(C), ref=.3)
	# plt.figure(figsize=(15, 5))
	# librosa.display.specshow(logC, sr=sr, x_axis='time', y_axis='cqt_note', fmin=fmin, cmap='coolwarm')
	# print("done!")
	# plt.show()

	# Directory to save frames
	frames_dir = "frames"
	if os.path.exists(frames_dir):
		shutil.rmtree(frames_dir)
	os.makedirs(frames_dir, exist_ok=True)
	S = librosa.util.normalize(C)

	rms = librosa.feature.rms(y=x, frame_length=hop_length, hop_length=hop_length)[0]
	# Normalize RMS values (optional, for consistent scale with the spectrogram)
	rms = (rms / numpy.max(rms)) * 0.2

	def apply_decay(previous_frame, decay_rate=0.2, decay_frames=6):
		decay_factor = decay_rate ** (1 / decay_frames)
		return previous_frame * decay_factor

	S_decayed = numpy.zeros_like(S)

	max_value = numpy.max(S)

	n_bins = len(S)
	image_height = 720
	image_width = 1280
	bar_width = image_width / (n_bins + 1)

	# Iterate over each frame in the spectrogram
	max_i = S.shape[1]
	print(f"generating {max_i} frames...")
	for i in range(max_i):
		if i > 0:
			S_decayed[:, i-1] = apply_decay(S_decayed[:, i-1])		
		S_decayed[:, i] = numpy.maximum(S[:, i], S_decayed[:, i-1])

		image = Image.new('RGB', (image_width, image_height), (255, 255, 255))
		draw = ImageDraw.Draw(image)


		for j, amplitude in enumerate(S_decayed[:, i]):
			color = get_color(j, n_bins)
			bar_height = int((amplitude / max_value) * image_height)
			left = j * bar_width
			draw.rectangle([left, image_height - bar_height, left + bar_width, image_height], fill=color)

		# Draw RMS amplitude as an additional bar
		if i < len(rms):
			rms_bar_height = int(rms[i] * image_height)
			left = n_bins * bar_width
			draw.rectangle([left, image_height - rms_bar_height, left + bar_width, image_height], fill=(0, 0, 255))

		image.save(f'{frames_dir}/frame_{i:04d}.png')

	print("creating video...")
	tempvid = "_temp.mp4"
	subprocess.run(f"ffmpeg -framerate 30 -i frames/frame_%04d.png -c:v libx264 -pix_fmt yuv420p {tempvid} -y -hide_banner -loglevel error")
	subprocess.run(f"ffmpeg -i {tempvid} -i {input_file} -c:v copy -c:a aac -strict experimental {output_file} -y -hide_banner -loglevel error")
	# subprocess.run(['start', "output.mp4"])
	# subprocess.run(f"ffmpeg -i {output_file} -i vocals_regualr.mp4 -filter_complex \"[0:v]scale=720:720[v0];[1:v]scale=720:720[v1];[v0][v1]hstack\" -c:v libx264 vocals_combined.mp4 -y -hide_banner -loglevel error")

	print("done!")

def process_all_wavs(directory):
	for filename in os.listdir(directory):
		if filename.endswith(".wav"):
			full_path = os.path.join(directory, filename)
			make_freq_vid(full_path)


# ffmpeg -i accompaniment.mp4 -i vocals.mp4 -filter_complex "[0:v]scale=720:720[v0];[1:v]scale=720:720[v1];[v0][v1]hstack" -c:v libx264 _temp.mp4 -y -hide_banner -loglevel error
# ffmpeg -i _temp.mp4 -i ../../dontlosesight.mp3 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest final.mp4 -y -hide_banner -loglevel error

process_all_wavs("..\\..\\data\\dls_output\\dontlosesight")
# make_freq_vid("..\\..\\data\\dls_output\\dontlosesight\\drums.wav")

# make_freq_vid("vocal_clip.wav")


# ffmpeg -i bass.mp4 -i drums.mp4 -i other.mp4 -i vocals.mp4 \
# -filter_complex \
# "[0:v]scale=1280:720,setpts=PTS-STARTPTS, pad=2560:1440 [a]; \
#  [1:v]scale=1280:720,setpts=PTS-STARTPTS [b]; \
#  [2:v]scale=1280:720,setpts=PTS-STARTPTS [c]; \
#  [3:v]scale=1280:720,setpts=PTS-STARTPTS [d]; \
#  [a][b]overlay=x=1280 [ab]; \
#  [ab][c]overlay=y=720 [abc]; \
#  [abc][d]overlay=x=1280:y=720" \
# -c:v libx264 _temp.mp4 -y -hide_banner -loglevel error && ffmpeg -i _temp.mp4 -i ../../dontlosesight.mp3 -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 -shortest FINAL.mp4 -y -hide_banner -loglevel error
