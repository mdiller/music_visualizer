import numpy as np
import re
import json
import librosa
import os

input_file = "songs/vocal_clip/vocal_clip.wav"
# input_file = "songs/dont_lose_sight/dont_lose_sight.mp3"


output_file = "src/generated/generated.js"
template_file = "scripts/template.js"
data_file = "songs/vocal_clip/data.npy"
temp_file = "scripts/index.html"


data_file = "src/generated/data.npy"

data: np.ndarray

if os.path.exists(data_file) and False:
	print("loading spectrogram from file...")
	data = np.load(data_file)
else:
	print("loading audio...")
	x, sr = librosa.load(input_file)

	fmin = librosa.midi_to_hz(9)
	framerate = 30
	bins_per_octave = 48
	octaves = 9
	n_bins = octaves * bins_per_octave
	hop_length = int(sr / framerate)

	print("doin spectrogram...")
	C = librosa.cqt(x, sr=sr, fmin=fmin, n_bins=n_bins, bins_per_octave=bins_per_octave, hop_length=hop_length)

	print("processing spectrogram...")
	C = librosa.amplitude_to_db(np.abs(C), ref=.6)

	C = librosa.util.normalize(C)

	decay_factor = 0.70  # Adjust this value as needed

	# Iterate through the frames (columns in C)
	for i in range(1, C.shape[1]):
		for j in range(C.shape[0]):
			# Apply decay if the current value is lower than the decayed previous value
			C[j, i] = max(C[j, i], C[j, i-1] * decay_factor)

	data = C.T
	
	data = np.maximum(data, 0)
	# data += np.min(data)
	data /= np.max(data)

	np.save(data_file, data)

# generate colors for gradients for scales
octave_count = 2
root_color = "#0000ff" # "#001e7d"
on_scale_color = "#004b7d"
off_scale_color = "#00cf7d"
hard_lines = False

note_thickness = 0.5

notes_per_scale = 12
# VERIFY that this adds up to 12 mebb?
major_scale_steps = [ 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1 ]
minor_scale_steps = [ 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1 ]

# COULD COLOR THIRDS ETC TOO
# could also color per-frame to get chords

# F Major
scale_steps = major_scale_steps
key_root_offset = 8 # how many half-steps up from A is the root of the key (F => )

steps_per_octave = len(scale_steps) # should be 12

colors = []
for i in range(steps_per_octave):
	color = on_scale_color if scale_steps[i] else off_scale_color
	if i == 0:
		color = root_color

	if note_thickness == 0:
		colors.append({
			"color": color,
			"percent": i / steps_per_octave
		})
	else:
		colors.append({
			"color": color,
			"percent": (i + (note_thickness / 2)) / steps_per_octave
		})
		colors.append({
			"color": color,
			"percent": (i - (note_thickness / 2)) / steps_per_octave
		})

for color in colors:
	percent = color["percent"]
	if key_root_offset != 0:
		percent += key_root_offset / steps_per_octave
	while percent < 0: 
		percent += 1
	while percent > 1:
		percent -= 1
	color["percent"] = percent

colors = sorted(colors, key=lambda c: c["percent"])

for color in colors:
	color["percent"] = f"{100 * color['percent']:.2f}%"

# if this works well:
# TODO: use https://github.com/jackmcarthur/musical-key-finder or similar to find what key the song is in, then color it based on that

# TODO: use librosa.beat.beat_track to get the beats of a song.

# TODO: have a serializable python class to represent the song data that can serialize to a np file and a json file next to it

gradients = [
	{
		"name": "MainScale",
		"colors": colors,
		"repeat": octave_count
	}
]

print("generating svg...")

# fit the sine data to the chart

svg_y_max = 100
svg_x_max = 600


def create_svg_path(frame_data):
	x_multiplier = svg_x_max / len(frame_data)
	# Start the path at the first point
	d = f"M0,{svg_y_max}"
	# Add line commands for each subsequent point
	for i, value in enumerate(frame_data):
		y_value = svg_y_max - int(value * svg_y_max)
		if y_value < 0:
			y_value = 0
		d += f" L{int(i * x_multiplier)},{y_value}"
	d += f"L{int((len(frame_data) - 1) * x_multiplier)},{svg_y_max}"
	d += f"Z"
	return d

# def create_svg_path_histogram(frame_data):
# 	# Start the path at the first point
# 	d = f"M0,{svg_y_max}"
# 	# Add line commands for each subsequent point
# 	for i, value in enumerate(frame_data):
# 		y_value = svg_y_max - int(value * svg_y_max)
# 		d += f" L{int(i * x_multiplier)},{y_value}"
# 		d += f" L{int((i + 1) * x_multiplier)},{y_value}"
# 	d += f"L{int((len(frame_data) - 1) * x_multiplier)},{svg_y_max}"
# 	d += f"Z"
# 	return d

# Generate SVG paths for each frame
svg_paths = [create_svg_path(frame) for frame in data]

# print("reading...") # HAVE THIS BE GENERATED FROM A TEMPLATE LATER:will make regex replacement much faster
# with open(temp_file, "r") as f:
# 	text = f.read()

# svg_paths_string = ",\n".join(map(lambda path: f"\"{path}\"", svg_paths))
# svg_paths_string = f"var SVG_PATHS = [\n{svg_paths_string}\n];"

# svg_paths_string += f"\nvar COLOR_GRADIENTS = {json.dumps(gradients)};\n"

# pattern = r"(// SVG_PATHS START\n)(.*?)(\n// SVG_PATHS END)"
# print("replacing...")
# text = re.sub(pattern, f"\\1{svg_paths_string}\\3", text, flags=re.DOTALL)


# print("writing...")
# with open(temp_file, "w+") as f:
# 	f.write(text)


print("reading...")
with open(template_file, "r") as f:
	text = f.read()

# svg_paths_string = ",\n".join(map(lambda path: f"\"{path}\"", svg_paths))
# svg_paths_string = f"export const SVG_PATHS = [\n{svg_paths_string}\n];"
pattern = r"(// SVG_PATHS START\n)(.*?)(\n// SVG_PATHS END)"
print("replacing...")


data_string = "";
# data_string = data.tolist()
# data_string = json.dumps(data_string);
# data_string = f"export const HIST_DATA = {data_string};"
data_string += f"export const COLOR_GRADIENTS = {json.dumps(gradients)};\n"

text = re.sub(pattern, data_string, text, flags=re.DOTALL)

print("writing...")
with open(output_file, "w+") as f:
	f.write(text)

print("done!")