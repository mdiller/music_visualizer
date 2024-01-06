import npyjs from 'npyjs';
import ndarray from 'ndarray';
import fs from 'fs';
import SONG_INFO from '../generated/song_info.json'

// const song_info_path = "songs/dont_lose_sight/song_info.json"

// var song_info_txt = await fs.readFile(song_info_path);
// var song_info = JSON.parse(song_info_txt);

console.log("hello!")

console.time("NumpyData load");

const n = new npyjs();
var spectrograms = [];
for (var i = 0; i < SONG_INFO.spectrograms.length; i++) {
	var spectrogram = SONG_INFO.spectrograms[i];
	var response = await n.load(`songs/dont_lose_sight/spectrograms/${spectrogram.name}.npy`);
	var data = ndarray(response.data, response.shape);
	var info = Object.assign({}, spectrogram );
	info.data = data;
	spectrograms.push(info);
}

console.timeEnd("NumpyData load");

// View2dfloat32

export const SPECTROGRAMS = spectrograms;