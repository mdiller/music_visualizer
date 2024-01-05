import {defineConfig} from 'vite';
import motionCanvas from '@motion-canvas/vite-plugin';
import ffmpeg from '@motion-canvas/ffmpeg';
// import fs from 'fs';
// import numpyLoader from './src/utils/numpyLoader'

// import npyjs from 'npyjs';
// import ndarray from 'ndarray';

// const numpyLoader = () => {
// 	return {
// 		name: 'numpy-loader',
// 		transform(src, id) {
// 			const [path, query] = id.split('?');
// 			if (query != 'numpy')
// 				return null;
//       console.log("hello123?")

// 			const data = fs.readFileSync(path);
// 			// const arrayBuffer = data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength);

// 			return {
//         code: "console.log('wtf')",
//         map: null
//       };
// 		}
// 	}
// };

export default defineConfig({
  plugins: [
    motionCanvas(),
    ffmpeg(),
    // numpyLoader()
  ],
});
