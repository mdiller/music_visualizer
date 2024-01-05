import {makeScene2D, Circle, Path, signal, Rect, Layout} from '@motion-canvas/2d';
import {all, createRef, createSignal, Vector2, waitFor} from '@motion-canvas/core';
import { FreqHistogram } from '../components/FreqHistogram';

export default makeScene2D(function* (view) {
  const frameIndex = createSignal(0);

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

  const histSize = new Vector2(canvas.width, 300);


  view.add(
    <Rect width={"100%"} height={"100%"} fill={"#15181e"}>
      <FreqHistogram
        strip={true}
        size={histSize}
        frame={frameIndex}
        position={[0 - (canvas.width / 2), (canvas.height / 2) - histSize.height]} />
    </Rect>
  );

  for (var i = 0; i < 200; i++) {
    frameIndex(i)
    yield* waitFor(1 / 30)
  }
});
