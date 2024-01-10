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
} from '@motion-canvas/core';
import { CoolGradient } from '../utils/CoolGradient';

import { NumpyData, StemInfo } from '../generated/DataClasses';

export interface PathEchoesProps extends NodeProps {
	size: SignalValue<Vector2>;
	percent: SignalValue<number>;
}

export class PathEchoes extends Node {	
	@signal()
	public declare readonly size: SimpleSignal<Vector2, this>;

	@signal()
	public declare readonly percent: SimpleSignal<number, this>;

	private readonly container = createRef<Rect>();

	public constructor(props?: PathEchoesProps) {
		super({
			...props,
		});
		const THECOUNT = 10;
		const spacing = 1;

		const gradient = CoolGradient.fromColors(["#13151b", "#0b0c0f"]);


		function makePath() {

		}// 67

		this.add(
			<Layout>
				{range(THECOUNT).map(index => {
					return <Path
						y={() => index * (this.size().height / (THECOUNT - spacing))}
						fill={() => gradient.getColorAt(index / THECOUNT)}
						data={() => {
							var size = this.size();
							var h = size.height;
							var w = size.width;
							return `m0,${h} L0,0 L${w},0 L${w},${h}`;
						}}
					></Path>
				})}
			</Layout>
		);
	}
}