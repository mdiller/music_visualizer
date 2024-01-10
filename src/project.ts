import {makeProject} from '@motion-canvas/core';

import example from './scenes/example?scene';

import { SONG_AUDIO } from './utils/SongLoader';

export default makeProject({
  scenes: [example],
  audio: SONG_AUDIO
});
