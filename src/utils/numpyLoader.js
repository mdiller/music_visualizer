

/** @type {import('vite').Plugin} */
export default function numpyLoader() {
	return {
		name: 'numpy-loader',
		transform(src, id) {
			const [path, query] = id.split('?');
			if (query != 'numpy')
				return null;

			const data = fs.readFileSync(path);
			const arrayBuffer = data.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);

			return arrayBuffer;
		}
	}
};