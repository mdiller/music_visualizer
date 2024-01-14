import npyjs from 'npyjs';
import ndarray from 'ndarray';
import fs from 'fs';
import SONG_INFO_JSON from '../generated/song_info.json'
import { NumpyData, SongInfo, StemInfo } from '../generated/DataClasses'
import { ThreadGenerator, waitFor } from '@motion-canvas/core';

import { MP3_FILE } from '../generated/song_mp3'

console.log("hello!")

console.time("SongData load");

// @ts-ignore
var song_info = new SongInfo(SONG_INFO_JSON);

var numpy_datas: NumpyData[] = [];

song_info.stems.forEach(stem => {
	numpy_datas.push(...stem.getDataProps());
});
song_info.poses.forEach(pose => {
	numpy_datas.push(...pose.getDataProps());
});

await Promise.all(numpy_datas.map(d => d.load()));


console.timeEnd("SongData load");

// View2dfloat32

export const STEMS = {
	bass: song_info.stems[0],
	drums: song_info.stems[1],
	other: song_info.stems[2],
	vocals: song_info.stems[3],
	song: song_info.stems[4],
};
export const SONG_NUMPY_DATAS = numpy_datas;
export const SONG_INFO = song_info;
export const SONG_AUDIO = MP3_FILE;