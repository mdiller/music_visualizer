# for processing videos of dancing into poses
import os
import subprocess
import json
import numpy as np

from data_classes import PoseInfo, NumpyData
from data_cache import NumpyCache, hash_string



ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
OPENPOSE_DIR = os.path.join(ROOT_DIR, "_temp", "openpose")
OPENPOSE_EXE = os.path.join(OPENPOSE_DIR, "bin", "OpenPoseDemo.exe")

# "C:\dev\projects\music_visualizer\_temp\openpose\bin\OpenPoseDemo.exe" --video ../test_2.mp4 --write_video ../out_test_1.avi --disable_blending --tracking 0 --number_people_max 1

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
		print(vid_name, vid_filename)
		out_mp4file = os.path.join(out_root, f"{vid_name}.mp4")

		if not os.path.exists(out_mp4file):
			command = f"ffmpeg -loglevel error -i {vid_filename} -map_metadata -1 {out_mp4file}"
			print(f"> {command}")
			subprocess.run(command, shell=True, check=True, cwd=OPENPOSE_DIR)

		out_jsondir = os.path.join(out_root, f"{vid_name}_jsons")
		out_avifile = os.path.join(out_root, f"{vid_name}.avi")

		if not os.path.exists(out_avifile):
			command = f"\"{OPENPOSE_EXE}\" --video {out_mp4file} --write_video {out_avifile} --write_json {out_jsondir} --disable_blending --tracking 0 --number_people_max 1"
			print(f"> {command}")
			subprocess.run(command, shell=True, check=True, cwd=OPENPOSE_DIR)
	
		
		out_numpyfile = os.path.join(out_root, f"{vid_name}.npy")

		if not os.path.exists(out_numpyfile):
			json_files = []
			for root, dirs, files in os.walk(out_jsondir):
				for file in files:
					json_files.append(os.path.join(root, file))
				break
			json_files.sort()
			
			frames = []
			for file in json_files:
				with open(file, "r") as f:
					data = json.loads(f.read())
				frames.append(data["people"][0]["pose_keypoints_2d"])
			
			np_data = np.array(frames)
			np.save(out_numpyfile, np_data)

		command = f"ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of json {out_mp4file}"
		print(f"> {command}")
		result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
		output = result.stdout
		info = json.loads(output)

		pose_info = PoseInfo()
		pose_info.width = info["streams"][0]["width"]
		pose_info.height = info["streams"][0]["height"]

		npy_data = NumpyData()
		npy_data.filename = os.path.relpath(os.path.abspath(out_numpyfile), ROOT_DIR)
		npy_data.framerate = float(eval(info["streams"][0]["r_frame_rate"]))
		npy_data.offset = 0

		pose_info.DATA_poseframes = npy_data
		pose_infos.append(pose_info)

	return pose_infos