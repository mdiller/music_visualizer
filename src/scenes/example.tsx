import {makeScene2D, Circle, Path, signal, Rect, Layout} from '@motion-canvas/2d';
import {all, Color, createRef, createSignal, map, ThreadGenerator, tween, Vector2, waitFor} from '@motion-canvas/core';
import { FreqHistogram } from '../components/FreqHistogram';
import { PathEchoes } from '../components/PathEchoes';
import { SimpleLine } from '../components/SimpleLine';
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

  const lineSize = new Vector2(canvas.width, 100);


  // #3b0c0f, 0b0c0f
  const background_gradient = CoolGradient.fromColors(["#13151b", "#13151b", "#131526", "#131534"]);

  const background_color = createSignal(new Color("#ff0000"))
  
  var volume_data = STEMS.song.DATA_volume_rolling_average;

  view.add(
    <Rect width={"100%"} height={"100%"} fill={background_color}>
      <PathEchoes 
        size={canvas}
        percent={percent_through}
        position={[canvas.width / -2, canvas.height / -2]}
      />
      <SimpleLine
        size={lineSize}
        percent_through={percent_through}
        line_data={volume_data} // line
        position={[0 - (canvas.width / 2), (canvas.height / 2) - histSize.height - lineSize.height - 50]} />
      <SimpleLine
        size={lineSize}
        percent_through={percent_through}
        line_data={STEMS.song.DATA_volume_velocity} // line
        position={[0 - (canvas.width / 2), (canvas.height / 2) - histSize.height]} />
      <FreqHistogram
        size={histSize}
        scale={[1, -1]}
        stem={STEMS.bass} // bass
        gradient={CoolGradient.fromScale("#4708d2", "#7f08d2", "#ab08d2")}
        position={[0 - (canvas.width / 2),  0 - ((canvas.height / 2) - histSize.height)]} />
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
        stem={STEMS.other} // other
        gradient={CoolGradient.fromColors(["#0e49be", "#ab08d2", "#0e49be"], true)}
        position={[0 - (canvas.width / 2), (canvas.height / 2) - histSize.height]} />
    </Rect>
  );

  background_color(() => {
    return background_gradient.getColorAt(STEMS.song.DATA_volume_rolling_average.valueSignal())
  });

  

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
    for (var i = 0; i < data.data.shape[0]; i++) {
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

  yield * all(...generators);
});
