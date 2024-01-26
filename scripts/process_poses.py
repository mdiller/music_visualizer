# for processing videos of dancing into poses
import os
import re
import subprocess
import json
import numpy as np

from data_classes import PoseInfo, NumpyData
from data_cache import NumpyCache, hash_string


POSE_PARTS = [ "pose", "hand_left", "hand_right" ]
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
OPENPOSE_DIR = os.path.join(ROOT_DIR, "_temp", "openpose")
OPENPOSE_EXE = os.path.join(OPENPOSE_DIR, "bin", "OpenPoseDemo.exe")

# "C:\dev\projects\music_visualizer\_temp\openpose\bin\OpenPoseDemo.exe" --video ../test_2.mp4 --write_video ../out_test_1.avi --disable_blending --tracking 0 --number_people_max 1

def rolling_average(data: np.ndarray, window_size: float) -> np.ndarray:
	original_size = len(data)
	data = np.convolve(data, np.ones(window_size), 'valid') / window_size
	pad_size = original_size - len(data)
	if pad_size > 0:
		last_value = data[-1]
		data = np.pad(data, (0, pad_size), 'constant', constant_values=last_value)
	return data

def rolling_average2d(data: np.ndarray, window_size: float) -> np.ndarray:
	shape = (data.shape[0] - window_size + 1, window_size, data.shape[1])
	strides = (data.strides[0], data.strides[0], data.strides[1])
	sliding_windows = np.lib.stride_tricks.as_strided(data, shape=shape, strides=strides)
	return sliding_windows.mean(axis=1)

def process_videos(SONG_ROOT: str, VIDEOS_DIR: str, OUT_DIR: str):
	videos = []
	for root, dirs, files in os.walk(VIDEOS_DIR):
		for file in files:
			videos.append((
				os.path.splitext(file)[0],
				os.path.join(root, file)))
		break
	
	out_root = os.path.join(VIDEOS_DIR, "_posedata")
	if not os.path.exists(out_root):
		os.makedirs(out_root)
	
	pose_infos = []
	for vid_name, vid_filename in videos:
		vid_offset = 0
		offset_pattern = "_offset([0-9.]+)$"
		match = re.search(offset_pattern, vid_name)
		if match:
			vid_name = re.sub(offset_pattern, "", vid_name)
			vid_offset = 0 - float(match.group(1))

		print(vid_name, vid_filename)
		out_mp4file = os.path.join(out_root, f"{vid_name}.mp4")

		CHANGED = False
		# if vid_name == "me3":
		# 	CHANGED = True
		if not os.path.exists(out_mp4file):
			command = f"ffmpeg -loglevel error -i {vid_filename} -map_metadata -1 {out_mp4file}"
			print(f"> {command}")
			subprocess.run(command, shell=True, check=True, cwd=OPENPOSE_DIR)
			CHANGED = True

		out_jsondir = os.path.join(out_root, f"{vid_name}_jsons")
		out_avifile = os.path.join(out_root, f"{vid_name}.avi")

		if CHANGED or not os.path.exists(out_jsondir):
			# --disable_blending (doesnt mix video with the avi bones output)
			# --display 0 (hides the window from popping up)
			# --hand (to also parse hands)
			# --net_resolution -1x320 (reduce memory usage and improve speed) 
			# --tracking 0 (increase this number to increase speed but decrease tracking accuracy)
			# --write_video {out_avifile} (write the video file)
			# --render_pose 0 (for if not writing video)
			posemodel = "COCO" # better is BODY_25 but takes more memory
			command = f"\"{OPENPOSE_EXE}\" --model_pose {posemodel} --video {out_mp4file} --write_json {out_jsondir} --display 0 --hand --tracking 0 --write_video {out_avifile} --number_people_max 1"
			print(f"> {command}")
			subprocess.run(command, shell=True, check=True, cwd=OPENPOSE_DIR)
			CHANGED = True
		
		print("get vid info")
		command = f"ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of json {out_mp4file}"
		result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
		output = result.stdout
		info = json.loads(output)

		pose_info = PoseInfo()
		pose_info.width = info["streams"][0]["width"]
		pose_info.height = info["streams"][0]["height"]
		framerate = float(eval(info["streams"][0]["r_frame_rate"]))

		for part_name in POSE_PARTS:
			vid_part_name = f"{vid_name}_{part_name}"
			out_numpyfile1 = os.path.join(out_root, f"{vid_part_name}.npy")
			if CHANGED or not os.path.exists(out_numpyfile1):
				print("processing pose numpy data...")
				json_files = []
				for root, dirs, files in os.walk(out_jsondir):
					for file in files:
						json_files.append(os.path.join(root, file))
					break
				json_files.sort()
				
				skipped_frames = 0
				frames = []
				for file in json_files:
					with open(file, "r") as f:
						data = json.loads(f.read())
					if len(data["people"]) < 1:
						# IF WE CANT FIND PEOPLE
						if len(frames) != 0:
							frames.append(frames[-1]) # append last frame
						else:
							skipped_frames += 1
							continue # skip frames till we found people
					else:
						frames.append(data["people"][0][f"{part_name}_keypoints_2d"])
				
				# backfill any skipped frames
				if skipped_frames > 0:
					for i in range(skipped_frames):
						frames.insert(0, frames[0])
				
				np_data = np.array(frames)

				np.save(out_numpyfile1, np_data)
				CHANGED = True
			
			out_numpyfile2 = os.path.join(out_root, f"{vid_part_name}_processed.npy")
			if CHANGED or not os.path.exists(out_numpyfile2):
				print("processing numpy data...")
				np_data = np.load(out_numpyfile1)
				np_data = rolling_average2d(np_data, 5)
				np.save(out_numpyfile2, np_data)
				CHANGED = True
			
			final_numpyfile = out_numpyfile2

			npy_data = NumpyData()
			npy_data.filename = os.path.relpath(os.path.abspath(final_numpyfile), ROOT_DIR)
			npy_data.framerate = framerate
			npy_data.offset = vid_offset
			setattr(pose_info, f"DATA_{part_name}", npy_data)

		pose_infos.append(pose_info)

	return pose_infos