import {makeScene2D, Circle, Path, signal, Rect, Layout} from '@motion-canvas/2d';
import {all, createRef, createSignal, Vector2, waitFor} from '@motion-canvas/core';
import { FreqHistogram } from '../components/FreqHistogram';

import { CoolGradient } from '../utils/CoolGradient';
import { SPECTROGRAMS } from '../utils/SongData';

export default makeScene2D(function* (view) {
  const frame = createSignal(0);

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


  view.add(
    <Rect width={"100%"} height={"100%"} fill={"#15181e"}>
      <FreqHistogram
        strip={true}
        size={histSize}
        frame={frame}
        scale={[1, -1]}
        spectrogram={SPECTROGRAMS[0]} // bass
        gradient={CoolGradient.fromScale("#4708d2", "#7f08d2", "#ab08d2")}
        position={[0 - (canvas.width / 2),  0 - ((canvas.height / 2) - histSize.height)]} />
      <FreqHistogram
        strip={true}
        size={drumHistSize}
        frame={frame}
        rotation={-90}
        spectrogram={SPECTROGRAMS[1]} // drums_right
        position={[(canvas.width / 2) - drumHistSize.y,  ((canvas.height / 2) - drumYBuffer)]} />
      <FreqHistogram
        strip={true}
        size={drumHistSize}
        frame={frame}
        rotation={-90}
        scale={[1, -1]}
        spectrogram={SPECTROGRAMS[1]} // drums_left
        position={[0 - ((canvas.width / 2) - drumHistSize.y),  ((canvas.height / 2) - drumYBuffer)]} />
      <FreqHistogram
        strip={true}
        size={vocalHistSize}
        frame={frame}
        spectrogram={SPECTROGRAMS[3]} // vocal_top
        gradient={CoolGradient.fromScale("#0e1ebe", "#0e49be", "#0e76be")}
        position={[vocalHistSize.x / -2, 0 - vocalHistSize.y]} />
      <FreqHistogram
        strip={true}
        size={vocalHistSize}
        frame={frame}
        scale={[1, -1]}
        spectrogram={SPECTROGRAMS[3]} // vocal_bottom
        gradient={CoolGradient.fromScale("#0e1ebe", "#0e49be", "#0e76be")}
        position={[vocalHistSize.x / -2, vocalHistSize.y]} />
      <FreqHistogram
        strip={true}
        size={histSize}
        frame={frame}
        spectrogram={SPECTROGRAMS[2]} // other
        gradient={CoolGradient.fromColors(["#0e49be", "#ab08d2", "#0e49be"], true)}
        position={[0 - (canvas.width / 2), (canvas.height / 2) - histSize.height]} />
    </Rect>
  );

  for (var i = 0; i < SPECTROGRAMS[4].frame_count; i++) {
    frame(i)
    yield* waitFor(1 / SPECTROGRAMS[4].framerate)
  }
});
