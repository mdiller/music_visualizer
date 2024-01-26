import {makeScene2D, Circle, Path, signal, Rect, Layout} from '@motion-canvas/2d';
import {all, Color, createRef, createSignal, map, ThreadGenerator, tween, Vector2, waitFor} from '@motion-canvas/core';
import { FreqGradient } from '../components/FreqGradient';
import { FreqHistogram } from '../components/FreqHistogram';
import { GradientEchoes } from '../components/GradientEchoes';
import { PathEchoes } from '../components/PathEchoes';
import { SimpleLine } from '../components/SimpleLine';
import { StickMan } from '../components/StickMan';
import { NumpyData } from '../generated/DataClasses';

import { CoolGradient } from '../utils/CoolGradient';
import { SONG_NUMPY_DATAS, SONG_INFO, STEMS } from '../utils/SongLoader';

export default makeScene2D(function* (view) {
  const percent_through = createSignal(0);
  const seconds = createSignal(0);

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
  const canvas = new Vector2(1920, 1080);


  const histHeight = 300;
  const histSize = new Vector2(canvas.width, 300);

  const drumYBuffer = (histHeight * .66)
  const drumHistSize = new Vector2(canvas.height - (drumYBuffer * 2), 500);

  const vocalHistSize = new Vector2(canvas.width - (drumHistSize.y * 2), 300);
  // vocalHistSize.width = canvas.width;

  const lineSize = new Vector2(canvas.width, 100);

  const manSize = new Vector2(1000, 1000);


  // #3b0c0f, 0b0c0f
  const background_gradient = CoolGradient.fromColors(["#13151b", "#13151b", "#131526", "#131534"]);

  const background_color = createSignal(new Color("#ff0000"))
  
  background_color(() => {
    return background_gradient.getColorAt(STEMS.song.DATA_volume_rolling_average.valueSignal())
  });

  var volume_data = STEMS.song.DATA_volume_rolling_average;

  view.add(
    <Rect width={"100%"} height={"100%"} fill={background_color}>
      {/* <GradientEchoes
        frameData={STEMS.drums.DATA_volume_detailed_average}
        size={canvas}
        percent={percent_through}
        opacity={0.5}
      /> */}
      <PathEchoes
        frameData={STEMS.drums.DATA_volume_detailed_average}
        size={canvas}
        percent={percent_through}
        position={[canvas.width / -2, canvas.height / -2]}
        gradient={() => {
          return CoolGradient.fromColors([background_color().hex(), background_color().hex(), "#131556", "#131571", "#131592"])
        }}
      />
      {/* <SimpleLine
        size={lineSize}
        percent_through={percent_through}
        line_data={volume_data} // line
        position={[0 - (canvas.width / 2), (canvas.height / 2) - histSize.height - lineSize.height - 50]} /> */}
      {/* <SimpleLine
        size={lineSize}
        percent_through={percent_through}
        line_data={STEMS.vocals.DATA_frequency_average} // line
        position={[0 - (canvas.width / 2), (canvas.height / 2) - histSize.height]} /> */}
      <FreqHistogram
        size={histSize}
        scale={[1, -1]}
        stem={STEMS.other} // other
        data_source={STEMS.other.DATA_peak_adjusted_spectrogram}
        gradient={CoolGradient.fromColors(["#0e49be", "#ab08d2", "#0e49be"], true)}
        position={[0 - (canvas.width / 2),  0 - ((canvas.height / 2) - histSize.height)]} />
      {/* <FreqGradient
        size={histSize}
        scale={[1, -1]}
        stem={STEMS.other} // other
        gradient={() => CoolGradient.fromColors(["#7f08d200", "#0e49be"])}
        position={[0 - (canvas.width / 2),  0 - ((canvas.height / 2) - histSize.height)]} /> */}
      <FreqHistogram
        size={drumHistSize}
        rotation={-90}
        stem={STEMS.drums} // drums_right
        position={[(canvas.width / 2) - drumHistSize.y,  ((canvas.height / 2) - drumYBuffer)]} />
      <FreqHistogram
        size={drumHistSize}
        rotation={-90}
        scale={[1, -1]}
        stem={STEMS.drums} // drums_left
        position={[0 - ((canvas.width / 2) - drumHistSize.y),  ((canvas.height / 2) - drumYBuffer)]} />
      <FreqHistogram
        size={vocalHistSize}
        stem={STEMS.vocals} // vocal_top
        gradient={CoolGradient.fromScale("#0e1ebe", "#0e49be", "#0e76be")}
        position={[vocalHistSize.x / -2, 0 - vocalHistSize.y]} />
      <FreqHistogram
        size={vocalHistSize}
        scale={[1, -1]}
        stem={STEMS.vocals} // vocal_bottom
        gradient={CoolGradient.fromScale("#0e1ebe", "#0e49be", "#0e76be")}
        position={[vocalHistSize.x / -2, vocalHistSize.y]} />
      <FreqHistogram
        size={histSize}
        stem={STEMS.bass} // base
        gradient={CoolGradient.fromScale("#4708d2", "#7f08d2", "#ab08d2")}
        position={[0 - (canvas.width / 2), (canvas.height / 2) - histSize.height]} />
      <StickMan
        size={manSize}
        percent_through={percent_through}
        pose_info={SONG_INFO.poses[2]}
        position={[(canvas.width / -2) + (manSize.width / 2), 0]}
      />
    </Rect>
  );

  

  var framerate = STEMS.song.framerate;
  var frame_count = STEMS.song.frame_count;
  var frames_wait_time = 1 / framerate;

  function* percentGenerator() {
    var total_seconds = (1 / framerate) * frame_count;
    yield* tween(total_seconds, value => {
      percent_through(value);
      seconds(value * total_seconds)
    });
  }

  var generators: ThreadGenerator[] = [];

  function *dataGenerator(data: NumpyData): ThreadGenerator {
    var start_index = 0;
    var offset_sec = data.offset; // seconds to offset the data by. negative means starts before song, positive means starts after
    if (offset_sec > 0) {
      yield* waitFor(offset_sec);
    }
    if (offset_sec < 0) {
      var frames_skipped = (0 - offset_sec) * data.framerate;
      start_index = Math.floor(frames_skipped) + 1;
      var time_til_next_frame = (start_index - frames_skipped) / data.framerate;
      yield* waitFor(time_til_next_frame);
    }

    for (var i = start_index; i < data.data.shape[0]; i++) {
      data.frameSignal(i);
      if (i < data.data.shape[0] - 1) {
        yield tween(1.0 / data.framerate, value => {
          data.valueSignal(map(data.data.get(i), data.data.get(i + 1), value))
        });
      }
      yield* waitFor(1.0 / data.framerate);
    }
  }

  generators.push(...SONG_NUMPY_DATAS.map(data => {
    return dataGenerator(data);
  }))

  generators.push(percentGenerator());
  // generators.push(pathEchoes().generator(STEMS.song.DATA_volume_rolling_average));

  yield * all(...generators);
});
