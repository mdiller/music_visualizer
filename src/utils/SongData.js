import npyjs from 'npyjs';
import ndarray from 'ndarray';
import fs from 'fs';
import SONG_INFO_JSON from '../generated/song_info.json'
import { SongInfo } from '../generated/DataClasses'

console.log("hello!")

console.time("SongData load");

var song_info = new SongInfo(SONG_INFO_JSON);

for (var i = 0; i < song_info.stems.length; i++) {
	await song_info.stems[i].load();
}

console.timeEnd("SongData load");

// View2dfloat32

export const SONG_INFO = song_info;