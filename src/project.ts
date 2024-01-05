import {makeProject} from '@motion-canvas/core';

import example from './scenes/example?scene';

import audio from '../songs/vocal_clip/vocal_clip.mp3'

export default makeProject({
  scenes: [example],
  audio: audio
});
