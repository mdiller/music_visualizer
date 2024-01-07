import npyjs from 'npyjs';
import ndarray from 'ndarray';
import fs from 'fs';
import SONG_INFO from '../generated/song_info.json'
import { SpectrogramInfo } from "../utils/SpectrogramInfo"

console.log("hello!")

console.time("SongData load");

const n = new npyjs();
var spectrograms = [];
for (var i = 0; i < SONG_INFO.spectrograms.length; i++) {
	var spectrogram = SONG_INFO.spectrograms[i];
	var response = await n.load(`songs/dont_lose_sight/spectrograms/${spectrogram.name}.npy`);
	var data = ndarray(response.data, response.shape);
	var info = Object.assign({}, spectrogram );
	info.data = data;
	spectrograms.push(new SpectrogramInfo(info));
}

console.timeEnd("SongData load");

// View2dfloat32

export const SPECTROGRAMS = spectrograms;