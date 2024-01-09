import {makeScene2D, Circle, Path, signal, Rect, Layout} from '@motion-canvas/2d';
import {all, Color, createRef, createSignal, Vector2, waitFor} from '@motion-canvas/core';
import { FreqHistogram } from '../components/FreqHistogram';
import { SimpleLine } from '../components/SimpleLine';

import { CoolGradient } from '../utils/CoolGradient';
import { SONG_INFO } from '../utils/SongData';

export default makeScene2D(function* (view) {
  const frame = createSignal(0);
  const percent_through = createSignal(0);

  const padding = 40;
//   <Rect width={"100%"} height={"100%"} fill={"#15181e"} gap={padding} padding={padding} direction={"column"} layout>
//   <Rect height={"100%"} gap={padding} direction={"row"} layout>
//     <Rect width={"100%"} height={"100%"} padding={padding} fill={'#282d39'}>
//       <FreqHistogram frame={frameIndex} />
//     </Rect>
//     <Rect width={"100%"} height={"100%"} fill={'#282d39'} />
//   </Rect>
//   <Rect height={"100%"} fill={'#282d39'} />
// </Rect>
  const canvas = {
    width: 1920,
    height: 1080
  };

  const histHeight = 300;
  const histSize = new Vector2(canvas.width, 300);

  const drumYBuffer = (histHeight * .66)
  const drumHistSize = new Vector2(canvas.height - (drumYBuffer * 2), 500);

  const vocalHistSize = new Vector2(canvas.width - (drumHistSize.y * 2), 300);

  const lineSize = new Vector2(canvas.width, 100);


  // #3b0c0f, 0b0c0f
  const background_gradient = CoolGradient.fromColors(["#15181e", "#242933", "#2a0933"]);

  const background_color = createSignal(new Color("#ff0000"))

  
  var volume_data = SONG_INFO.stems[4].DATA_volume_rolling_average;

  console.log(volume_data.shape[0]);

  view.add(
    <Rect width={"100%"} height={"100%"} fill={background_color}>
      <FreqHistogram
        size={histSize}
        frame={frame}
        scale={[1, -1]}
        stem={SONG_INFO.stems[0]} // bass
        gradient={CoolGradient.fromScale("#4708d2", "#7f08d2", "#ab08d2")}
        position={[0 - (canvas.width / 2),  0 - ((canvas.height / 2) - histSize.height)]} />
      <FreqHistogram
        size={drumHistSize}
        frame={frame}
        rotation={-90}
        stem={SONG_INFO.stems[1]} // drums_right
        position={[(canvas.width / 2) - drumHistSize.y,  ((canvas.height / 2) - drumYBuffer)]} />
      <FreqHistogram
        size={drumHistSize}
        frame={frame}
        rotation={-90}
        scale={[1, -1]}
        stem={SONG_INFO.stems[1]} // drums_left
        position={[0 - ((canvas.width / 2) - drumHistSize.y),  ((canvas.height / 2) - drumYBuffer)]} />
      <FreqHistogram
        size={vocalHistSize}
        frame={frame}
        stem={SONG_INFO.stems[3]} // vocal_top
        gradient={CoolGradient.fromScale("#0e1ebe", "#0e49be", "#0e76be")}
        position={[vocalHistSize.x / -2, 0 - vocalHistSize.y]} />
      <FreqHistogram
        size={vocalHistSize}
        frame={frame}
        scale={[1, -1]}
        stem={SONG_INFO.stems[3]} // vocal_bottom
        gradient={CoolGradient.fromScale("#0e1ebe", "#0e49be", "#0e76be")}
        position={[vocalHistSize.x / -2, vocalHistSize.y]} />
      <FreqHistogram
        size={histSize}
        frame={frame}
        stem={SONG_INFO.stems[2]} // other
        gradient={CoolGradient.fromColors(["#0e49be", "#ab08d2", "#0e49be"], true)}
        position={[0 - (canvas.width / 2), (canvas.height / 2) - histSize.height]} />
      <SimpleLine
        size={lineSize}
        percent_through={percent_through}
        line_data={volume_data} // line
        position={[0 - (canvas.width / 2), (canvas.height / 2) - histSize.height - lineSize.height - 50]} />
      <SimpleLine
        size={lineSize}
        percent_through={percent_through}
        line_data={SONG_INFO.stems[4].DATA_volume} // line
        position={[0 - (canvas.width / 2), (canvas.height / 2) - histSize.height]} />
    </Rect>
  );

  var framerate = SONG_INFO.stems[4].framerate;
  var frame_count = SONG_INFO.stems[4].frame_count;
  var frames_wait_time = 1 / framerate;

  // TODO: FIX THIS TO WORK PROPERLY (probably each DATA_ thing can return its own generator)
  // var generators = [];

  var volume_framerate = (frames_wait_time * frame_count) / volume_data.shape[0];
  // for (var i = 0; i < volume_data.shape[0]; i++) {
  //   generators.push(background_color(new Color(background_gradient.getColorAt(volume_data.get(i))), 1 / volume_framerate));
  //   // yield* waitFor(1 / volume_framerate);
  // }

  for (var i = 0; i < frame_count; i++) {
    frame(i)
    percent_through(i / frame_count)
    background_color(new Color(background_gradient.getColorAt(volume_data.get(Math.floor((i / frame_count) * volume_data.shape[0])))));
    yield* waitFor(frames_wait_time)
  }

  // yield * all(...generators);
});
