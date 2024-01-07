import {
	Node,
	NodeProps,
	initial,
	signal,
	Path,
	Rect,
	Txt,
	Gradient,
	Vector2LengthSignal,
} from '@motion-canvas/2d';
import {
	SignalValue,
	SimpleSignal,
	createRef,
	createSignal,
	createComputedAsync,
	map,
	Vector2,
} from '@motion-canvas/core';
import { COLOR_GRADIENTS } from '../generated/generated';
import { CoolGradient } from '../utils/CoolGradient';

// import { NUMPY_DATA } from '../utils/NumpyData'
import { SPECTROGRAMS } from '../utils/SongData';
import { SpectrogramInfo } from '../utils/SpectrogramInfo';

function createPathData(spectrogram: SpectrogramInfo, index: number, width: number, height: number): string {
	var data = spectrogram.data;
	var frameLength = data.shape[1];
	var x_range = spectrogram.max_x - spectrogram.min_x
	var xMultiplier = width / x_range;
	var x_floor = spectrogram.min_x;
	// console.log(frameLength, xMultiplier, x_range, x_floor);
	
	let d = `M0,${height}`;

	let lastXValue = 0;
	for (var i = spectrogram.min_x; i < spectrogram.max_x; i++) {
		let yValue = height - Math.floor(data.get(index, i) * height);
		let xValue = Math.floor((i - x_floor) * xMultiplier)
		if (yValue < 0) {
			yValue = 0;
		}
		if (yValue > 0) {
			lastXValue = xValue;
		}
		d += ` L${xValue},${yValue}`;
	}

	d += `L${lastXValue},${height}`;
	d += 'Z';

	return d;
}

export interface FreqHistogramProps extends NodeProps {
	frame: SignalValue<number>;
	spectrogram: SignalValue<SpectrogramInfo>;
	gradient?: SignalValue<CoolGradient>;
	size: SignalValue<Vector2>;
	strip?: SignalValue<boolean>;
}

export class FreqHistogram extends Node {
	@signal()
	public declare readonly frame: SimpleSignal<number, this>;

	@signal()
	public declare readonly spectrogram: SimpleSignal<SpectrogramInfo, this>;

	@initial(CoolGradient.fromColors([ "#0e49be", "#ab08d2" ]))
	@signal()
	public declare readonly gradient: SimpleSignal<CoolGradient, this>;
	
	@signal()
	public declare readonly size: SimpleSignal<Vector2, this>;
	
	@initial(false)
	@signal()
	public declare readonly strip: SimpleSignal<boolean, this>;

	private readonly container = createRef<Rect>();
	private readonly path = createRef<Path>();
	// TODO: make this into a "computed" method
	private readonly data = createSignal(() => createPathData(this.spectrogram(), this.frame(), this.size().x, this.size().y));
	// private readonly data = createSignal(() => createPathData(NUMPY_DATA, this.frame(), this.size().x, this.size().y));

	public constructor(props?: FreqHistogramProps) {
		super({
			...props,
		});

		// TODO: auto-compute these gradients from the data
		// const gradient = new Gradient({
		// 	type: 'linear',
		// 	fromX: this.size().x,
		// 	toX: this.size().y,
		// 	stops: [
		// 		{offset: 0, color: '#ab08d2'},
		// 		{offset: 0.5, color: '#0e49be'},
		// 		{offset: 1, color: '#ab08d2'}
		// 	]
		//   });

		this.add(
			<Path
				ref={this.path}
				fill={() => this.gradient().toGradient(this.size().x, this.spectrogram())}
				data={() => this.data()}
			></Path>
		);
	}
}