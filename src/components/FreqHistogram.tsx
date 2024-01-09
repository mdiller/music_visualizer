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
import { CoolGradient } from '../utils/CoolGradient';

import { StemInfo } from '../generated/DataClasses';

function createPathData(stem_info: StemInfo, index: number, width: number, height: number): string {
	var data = stem_info.DATA_spectrogram;
	var frameLength = data.shape[1];
	var x_range = stem_info.max_x - stem_info.min_x
	var xMultiplier = width / x_range;
	var x_floor = stem_info.min_x;
	// console.log(frameLength, xMultiplier, x_range, x_floor);
	
	let d = `M0,${height}`;

	let lastXValue = 0;
	for (var i = stem_info.min_x; i < stem_info.max_x; i++) {
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
	stem: SignalValue<StemInfo>;
	gradient?: SignalValue<CoolGradient>;
	size: SignalValue<Vector2>;
}

export class FreqHistogram extends Node {
	@signal()
	public declare readonly frame: SimpleSignal<number, this>;

	@signal()
	public declare readonly stem: SimpleSignal<StemInfo, this>;

	@initial(CoolGradient.fromColors([ "#0e49be", "#ab08d2" ]))
	@signal()
	public declare readonly gradient: SimpleSignal<CoolGradient, this>;
	
	@signal()
	public declare readonly size: SimpleSignal<Vector2, this>;

	private readonly container = createRef<Rect>();
	private readonly path = createRef<Path>();
	// TODO: make this into a "computed" method
	private readonly data = createSignal(() => createPathData(this.stem(), this.frame(), this.size().x, this.size().y));

	public constructor(props?: FreqHistogramProps) {
		super({
			...props,
		});

		this.add(
			<Path
				ref={this.path}
				fill={() => this.gradient().toGradient(this.size().x, this.stem())}
				data={() => this.data()}
			></Path>
		);
	}
}