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
	Layout,
	GradientStop,
} from '@motion-canvas/2d';
import {
	SignalValue,
	SimpleSignal,
	createRef,
	createSignal,
	createComputedAsync,
	map,
	Vector2,
	range,
	ThreadGenerator,
	waitFor,
	tween,
	Color,
	easeOutCubic,
	makeRef,
} from '@motion-canvas/core';
import { CoolGradient } from '../utils/CoolGradient';

import { SONG_NUMPY_DATAS, SONG_INFO, STEMS } from '../utils/SongLoader';
import { NumpyData, StemInfo } from '../generated/DataClasses';
import path from 'path';

export interface GradientEchoesProps extends NodeProps {
	size: SignalValue<Vector2>;
	percent: SignalValue<number>;
	frameData: SignalValue<NumpyData>;
}

const THECOUNT = 50;

class PathInfo {
	offset: number;
	color: any;

	constructor() {
		this.offset = 0;
		this.color = new Color("#00000000");
	}
}

export class GradientEchoes extends Node {	
	@signal()
	public declare readonly size: SimpleSignal<Vector2, this>;

	@signal()
	public declare readonly percent: SimpleSignal<number, this>;

	@signal()
	private readonly frameData: SimpleSignal<NumpyData, this>;
	
	private readonly stops: SimpleSignal<GradientStop[]> = createSignal(() => {
		const color_gradient = CoolGradient.fromColors(["#0f1015", "#13151b", "#131534", "#131545", "#131556"]);
		// const color_gradient = CoolGradient.fromColors(["#13151b", "#13151b", "#0000ff"]);
		var percent = this.percent();
		var data = this.frameData().data;
		var height = this.size().height;

		return range(THECOUNT).map(pathIndex => { // index 0 is at the top
			// () => index * (this.size().height / (THECOUNT - spacing))
			var frame = Math.floor(percent * data.shape[0]) - pathIndex;
			var stop = {
				offset: 0,
				color: color_gradient.getColorAt(0)
			};

			if (frame < 0) {
				return stop;
			}
			var percent_up = ((percent * data.shape[0]) - frame) / THECOUNT;

			stop.offset = easeOutCubic(percent_up);
			stop.color = color_gradient.getColorAt(data.get(frame));
			
			return stop;
		});
	})

	private readonly container = createRef<Rect>();



	public constructor(props?: GradientEchoesProps) {
		super({
			...props,
		});

		const paths: Path[] = [];
		var container = createRef<Layout>()

		var y_scale = 7;

		this.add(
			<Rect
				fill={() => new Gradient({
					type: 'radial',
					from: 0,
					toRadius: (this.size().height * y_scale),
					stops: this.stops()
				})}
				size={[this.size().width, this.size().height * y_scale]}
				scaleY={() => 1 / (y_scale / 2)}
				y={() => this.size().height / 2}
				ref={container}>
			</Rect>
		);
		
		container().filters.blur(() => 10);
		// paths.forEach(path => path.filters.blur(() => 5));
	}
}