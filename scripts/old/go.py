import numpy as np
import re
import json

# Constants
num_frames = 500  # Total number of arrays (frames)
length = 100      # Length of each array
frequency = 5     # Frequency of the sine wave
phase_shift = 0.3 # Phase shift for each new frame

# Generating the 2D numpy array
data = np.array([np.sin(2 * np.pi * frequency * (np.arange(length) / length) + phase_shift * frame)
						 for frame in range(num_frames)])

np.save("data.npy", data)

data = np.load("data.npy")


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

# TODO: have a serializable python class to represent the song data that can serialize to a numpy file and a json file next to it

gradients = [
	{
		"name": "MainScale",
		"colors": colors,
		"repeat": octave_count
	}
]

print("generating svg...")
# fit the sine data to the chart
data += np.abs(np.min(data))
data /= np.max(data)

svg_y_max = 100
svg_x_max = 600

x_multiplier = svg_x_max / len(data[0])

def create_svg_path(frame_data):
	# Start the path at the first point
	d = f"M0,{svg_y_max}"
	# Add line commands for each subsequent point
	for i, value in enumerate(frame_data):
		y_value = svg_y_max - int(value * svg_y_max)
		d += f" L{int(i * x_multiplier)},{y_value}"
	d += f"L{int((len(frame_data) - 1) * x_multiplier)},{svg_y_max}"
	d += f"Z"
	return d

def create_svg_path_histogram(frame_data):
	# Start the path at the first point
	d = f"M0,{svg_y_max}"
	# Add line commands for each subsequent point
	for i, value in enumerate(frame_data):
		y_value = svg_y_max - int(value * svg_y_max)
		d += f" L{int(i * x_multiplier)},{y_value}"
		d += f" L{int((i + 1) * x_multiplier)},{y_value}"
	d += f"L{int((len(frame_data) - 1) * x_multiplier)},{svg_y_max}"
	d += f"Z"
	return d

# Generate SVG paths for each frame
svg_paths = [create_svg_path(frame) for frame in data]

print("reading...") # HAVE THIS BE GENERATED FROM A TEMPLATE LATER:will make regex replacement much faster
with open("index.html", "r") as f:
	text = f.read()

svg_paths_string = ",\n".join(map(lambda path: f"\"{path}\"", svg_paths))
svg_paths_string = f"var SVG_PATHS = [\n{svg_paths_string}\n];"

svg_paths_string += f"\nvar COLOR_GRADIENTS = {json.dumps(gradients)};\n"

pattern = r"(// SVG_PATHS START\n)(.*?)(\n// SVG_PATHS END)"

print("replacing...")
text = re.sub(pattern, f"\\1{svg_paths_string}\\3", text, flags=re.DOTALL)

print("writing...")
with open("index.html", "w+") as f:
	f.write(text)

print("done!")