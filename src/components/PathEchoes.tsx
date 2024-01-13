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

const THECOUNT = 50;

class PathInfo {
	y_offset: number;
	color: any;
	data: string;
	z_index: number;

	constructor() {
		this.y_offset = 0;
		this.color = new Color("#00000000");
		this.data = "M0,0 L1,1";
		this.z_index = 0;
	}
}


export interface PathEchoesProps extends NodeProps {
	size: SignalValue<Vector2>;
	percent: SignalValue<number>;
	frameData: SignalValue<NumpyData>;
	gradient: SignalValue<CoolGradient>;
}

export class PathEchoes extends Node {	
	@signal()
	public declare readonly size: SimpleSignal<Vector2, this>;

	@signal()
	public declare readonly percent: SimpleSignal<number, this>;

	@signal()
	private readonly frameData: SimpleSignal<NumpyData, this>;

	@signal()
	private readonly gradient: SimpleSignal<CoolGradient, this>;
	
	private readonly pathInfos: SimpleSignal<PathInfo[]> = createSignal(() => {
		// const color_gradient = CoolGradient.fromColors(["#0f1015", "#13151b", "#131534", "#131545", "#131556"]);
		// const color_gradient = CoolGradient.fromColors(["#0f1015", "#0f1015", "#131534", "#131545", "#131556"]);


		// const color_gradient = CoolGradient.fromColors(["#0f1015", "#0f1015", "#131556", "#131571", "#131592"]);

		const color_gradient = this.gradient();

		// const color_gradient = CoolGradient.fromColors(["#13151b", "#13151b", "#0000ff"]);
		var percent = this.percent();
		var data = this.frameData().data;
		var height = this.size().height;

		return range(THECOUNT).map(pathIndex => { // index 0 is at the top
			// () => index * (this.size().height / (THECOUNT - spacing))
			var frame = Math.floor(percent * data.shape[0]) - pathIndex;
			var pathInfo = new PathInfo();

			if (frame < 0) {
				pathInfo.color = color_gradient.getColorAt(0);
				return pathInfo;
			}

			var percent_up = ((percent * data.shape[0]) - frame) / THECOUNT;

			pathInfo.y_offset = map(height, -200, easeOutCubic(percent_up));

			// var color1 = color_gradient.getColorAt(data.get(frame));
			// var color2 = color_gradient.getColorAt(data.get(frame - 1));
			// pathInfo.color = new Gradient({
			// 	type: 'linear',
			// 	fromY: 0,
			// 	toY: height,
			// 	stops: [
			// 		{ color: color2, offset: 0 },
			// 		{ color: color1, offset: 5 / THECOUNT },
			// 		{ color: color1, offset: 1 }
			// 	]
			// });
			pathInfo.color = color_gradient.getColorAt(data.get(frame));
			
			var size = this.size();
			var h = size.height;
			var w = size.width;
			// pathInfo.data = `m0,${h} L0,0 L${w},0 L${w},${h}`;
			var thing = 200;
			pathInfo.data = `m0,${h} L0,${thing} Q ${w/2}, 0 ${w},${thing} L${w},${h}`;
			pathInfo.z_index = THECOUNT - pathIndex;
			
			return pathInfo;
		});
	})

	private readonly container = createRef<Rect>();



	public constructor(props?: PathEchoesProps) {
		super({
			...props,
		});

		const paths: Path[] = [];
		var container = createRef<Layout>()

		this.add(
			<Layout ref={container}>
				{range(THECOUNT).map(i => { // index 0 is at the top
						return <Path
							zIndex={() => this.pathInfos()[i].z_index}
							// stroke={"#00ff00"}
							// lineWidth={4}
							y={() => this.pathInfos()[i].y_offset}
							fill={() => this.pathInfos()[i].color}
							data={() => this.pathInfos()[i].data}
							ref={makeRef(paths, i)}
						></Path>
					})
				}
			</Layout>
		);
		
		container().filters.blur(() => 10);
		// paths.forEach(path => path.filters.blur(() => 5));
	}
}