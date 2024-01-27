# for processing videos of dancing into poses
import os
import re
import subprocess
import json
import numpy as np

from utils.smart_stepper import DataStub, SmartStepper
from utils.data_classes import PoseInfo, NumpyData
from utils.data_cache import NumpyCache, hash_string
import utils.numpytools as numpytools


POSE_PARTS = [ "pose", "hand_left", "hand_right" ]
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
OPENPOSE_DIR = os.path.join(ROOT_DIR, "_temp", "openpose")
OPENPOSE_EXE = os.path.join(OPENPOSE_DIR, "bin", "OpenPoseDemo.exe")
VIDEOS_DIR = os.path.join(ROOT_DIR, "data", "videos")

# "C:\dev\projects\music_visualizer\_temp\openpose\bin\OpenPoseDemo.exe" --video ../test_2.mp4 --write_video ../out_test_1.avi --disable_blending --tracking 0 --number_people_max 1

class PoseProcessor(SmartStepper):
	info: PoseInfo
	def __init__(self, name: str):
		super().__init__(f"Pose - {name}", os.path.join(VIDEOS_DIR, "data", name), PoseInfo)
		self.name = name
		self.filename = os.path.join(VIDEOS_DIR, f"{name}.mp4")
	
	def STEP_run_openpose(self):		
		out_root = self.out_dir
		out_mp4file = os.path.join(out_root, f"{self.name}.mp4")

		command = f"ffmpeg -loglevel error -i {self.filename} -map_metadata -1 {out_mp4file} -y"
		self.print(f"> {command}")
		subprocess.run(command, shell=True, check=True, cwd=OPENPOSE_DIR)

		out_jsondir = os.path.join(out_root, f"{self.name}_jsons")
		out_avifile = os.path.join(out_root, f"{self.name}.avi")

		# --disable_blending (doesnt mix video with the avi bones output)
		# --display 0 (hides the window from popping up)
		# --hand (to also parse hands)
		# --net_resolution -1x320 (reduce memory usage and improve speed) 
		# --tracking 0 (increase this number to increase speed but decrease tracking accuracy)
		# --write_video {out_avifile} (write the video file)
		# --render_pose 0 (for if not writing video)
		posemodel = "BODY_25" # better is BODY_25 but takes more memory than COCO
		command = f"\"{OPENPOSE_EXE}\" --model_pose {posemodel} --video {out_mp4file} --write_json {out_jsondir} --display 0 --tracking 0 --write_video {out_avifile} --number_people_max 1"
		self.print(f"> {command}")
		subprocess.run(command, shell=True, check=True, cwd=OPENPOSE_DIR)
		
		self.print("get vid info")
		command = f"ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of json {out_mp4file}"
		result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
		output = result.stdout
		info = json.loads(output)

		self.info.width = info["streams"][0]["width"]
		self.info.height = info["streams"][0]["height"]
		self.info.framerate = float(eval(info["streams"][0]["r_frame_rate"]))

		return np.empty(5) # just some dummy data so that we can detect when dependancies of this step need to update
	
	def STEP_read_openpose_data(self, STEP_run_openpose: NumpyCache):
		# for part_name in POSE_PARTS:
		part_name = "pose"
		vid_part_name = f"{self.name}_{part_name}"
		out_jsondir = os.path.join(self.out_dir, f"{self.name}_jsons")
		
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

		return np_data
	
	def STEP_rolling_average(self, STEP_read_openpose_data: NumpyCache):
		data = STEP_read_openpose_data.read()
		data = numpytools.rolling_average2d(data, 5)
		return data

	def STEP_anim_normalize(self, STEP_rolling_average: NumpyCache):
		data = STEP_rolling_average.read()
		if not ("anim" in self.name):
			return data
		
		nums_per_pt = 3
		points_per_frame = int(data.shape[1] / nums_per_pt)
		body_center_x_index = 1 * nums_per_pt # index 1 (body center) * 3 cuz we got 3 values per point, + 0 to get X
		frame_count = data.shape[0]

		start_x = data[0][body_center_x_index]
		end_x = data[frame_count - 1][body_center_x_index]
		diff_x = (start_x - end_x)

		# adjust the due so he doesnt move horizontally
		for i in range(frame_count):
			percent = i / (frame_count - 1)
			x_mod = diff_x * percent
			for j in range(points_per_frame):
				data[i][j * nums_per_pt] += x_mod
		
		return data


	
	def STEP_pose(self, STEP_anim_normalize: NumpyCache):
		data = STEP_anim_normalize.read()
		vid_offset = 0
		offset_pattern = "_offset([0-9.]+)$"
		match = re.search(offset_pattern, self.name)
		if match:
			vid_offset = vid_offset = 0 - float(match.group(1))
		
		return DataStub(data, self.info.framerate, vid_offset)
		

def process_videos(SONG_ROOT: str, VIDEOS_DIR: str, OUT_DIR: str):
	videos = []
	for root, dirs, files in os.walk(VIDEOS_DIR):
		for file in files:
			videos.append((
				os.path.splitext(file)[0],
				os.path.join(root, file)))
		break
	
	pose_infos = []
	for vid_name, vid_filename in videos:
		processor = PoseProcessor(vid_name)
		pose_infos.append(processor.run())

	return pose_infos