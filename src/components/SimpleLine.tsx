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

import { NumpyData, StemInfo } from '../generated/DataClasses';

function createPathData(data_info: NumpyData, percent_through: number, width: number, height: number): string {
	var data = data_info.data;
	var dataLength = data.shape[0];
	// console.log(data.get(2))
	var xMultiplier = width;
	
	let d = `M0,${height}`;

	let lastXValue = 0;
	for (var i = 0; i < dataLength; i++) {
		let yValue = height - Math.floor(data.get(i) * height);
		let xValue = Math.floor((i / dataLength) * xMultiplier)
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

export interface SimpleLineProps extends NodeProps {
	percent_through: SignalValue<number>;
	line_data: SignalValue<NumpyData>;
	gradient?: SignalValue<CoolGradient>;
	size: SignalValue<Vector2>;
}

export class SimpleLine extends Node {
	@signal()
	public declare readonly percent_through: SimpleSignal<number, this>;

	@signal()
	public declare readonly line_data: SimpleSignal<NumpyData, this>;

	@initial(CoolGradient.fromColors([ "#ab08d2", "#ab08d2" ]))
	@signal()
	public declare readonly gradient: SimpleSignal<CoolGradient, this>;
	
	@signal()
	public declare readonly size: SimpleSignal<Vector2, this>;

	private readonly container = createRef<Rect>();
	private readonly path = createRef<Path>();
	private readonly data = createSignal(() => createPathData(this.line_data(), this.percent_through(), this.size().x, this.size().y));

	public constructor(props?: SimpleLineProps) {
		super({
			...props,
		});

		this.add(
			<Rect>
				<Path
					ref={this.path}
					fill={"#0e49be"}
					data={() => this.data()}
				></Path>,
				<Rect>
					<Rect position={() => [ this.percent_through() * this.size().width, this.size().height / 2 ]} size={[3, this.size().height]} fill={'#ff000044'} />
				</Rect>
			</Rect>
		);
	}
}