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
import { NUMPY_DATA } from '../utils/NumpyData'

function createPathData(data: any, index: number, width: number, height: number): string {
	var frameLength = data.shape[1];
	var xMultiplier = width / frameLength
	console.log(frameLength);
	
	let d = `M0,${height}`;

	for (var i = 0; i < frameLength; i++) {
		let yValue = height - Math.floor(data.get(index, i) * height);
		if (yValue < 0) {
			yValue = 0;
		}
		d += ` L${Math.floor(i * xMultiplier)},${yValue}`;
	}

	d += `L${Math.floor((frameLength - 1) * xMultiplier)},${height}`;
	d += 'Z';

	return d;
}

export interface FreqHistogramProps extends NodeProps {
	frame: SignalValue<number>;
	size: SignalValue<Vector2>;
	strip?: SignalValue<boolean>;
}

export class FreqHistogram extends Node {
	@signal()
	public declare readonly frame: SimpleSignal<number, this>;
	
	@signal()
	public declare readonly size: SimpleSignal<Vector2, this>;
	
	@initial(false)
	@signal()
	public declare readonly strip: SimpleSignal<boolean, this>;

	private readonly container = createRef<Rect>();
	private readonly path = createRef<Path>();

	// TODO: make this into a "computed" method
	private readonly data = createSignal(() => createPathData(NUMPY_DATA, this.frame(), this.size().x, this.size().y));

	public constructor(props?: FreqHistogramProps) {
		super({
			...props,
		});

		// TODO: auto-compute these gradients from the data
		const gradient = new Gradient({
			type: 'linear',
			fromX: this.size().x,
			toX: this.size().y,
			stops: [
				{offset: 0, color: '#00ff00'},
				{offset: 0.5, color: '#00ff00'},
				{offset: 1, color: '#ff0000'}
			]
		  });

		this.add(
			<Path
				ref={this.path}
				fill={gradient}
				data={() => this.data()}
			></Path>
		);
	}
}