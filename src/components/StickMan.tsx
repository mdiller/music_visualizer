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
	Circle,
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

import { PoseInfo } from '../generated/DataClasses';
import { StickManRigger, StickManModel } from '../utils/StickManRigging';
import { PathInfo } from '../utils/svgtools';

const STICKMAN_RIGGER = new StickManRigger(StickManModel.BONES);

export interface StickManProps extends NodeProps {
	percent_through: SignalValue<number>;
	size: SignalValue<Vector2>;
	pose_info: SignalValue<PoseInfo>;
}

export class StickMan extends Node {
	@signal()
	public declare readonly percent_through: SimpleSignal<number, this>;
	
	@signal()
	public declare readonly size: SimpleSignal<Vector2, this>;
	
	@signal()
	public declare readonly pose_info: SimpleSignal<PoseInfo, this>;

	// the points array for this frame
	private readonly framePoints: SimpleSignal<Vector2[]> = createSignal(() => {
		var pose_info = this.pose_info();
		var out_size = this.size();
		var frame = pose_info.DATA_pose.frameSignal();
		var posedata = pose_info.DATA_pose.data;
		
		// can extract this to a separate calculated variable
		var in_aspect = pose_info.width / pose_info.height;
		var out_aspect = out_size.width / out_size.height;
		var out_path_size = null;
		var points_offset = null;
		if (in_aspect > out_aspect) { // space on top/bottom
			out_path_size = new Vector2(out_size.width, out_size.width / in_aspect);
			points_offset = new Vector2(0, (out_size.height - out_path_size.height) / 2);
		}
		else { // space on left/right
			out_path_size = new Vector2(out_size.height * in_aspect, out_size.height);
			points_offset = new Vector2((out_size.width - out_path_size.width) / 2, 0);
		}
		var points_multiplier = new Vector2(out_path_size.width / pose_info.width, out_path_size.height / pose_info.height);
		
		var points: Vector2[] = [];
		for (var i = 0; i < posedata.shape[1]; i += 3) {
			points.push(new Vector2(
				points_offset.x + (posedata.get(frame, i) * points_multiplier.x),
				points_offset.y + (posedata.get(frame, i + 1) * points_multiplier.y)
			));
		}
		return points;
	});

	private readonly pathsInfo: SimpleSignal<PathInfo[]> = createSignal(() => {
		return STICKMAN_RIGGER.render(this.framePoints());
	});

	private readonly container = createRef<Rect>();
	private readonly path = createRef<Path>();

	public constructor(props?: StickManProps) {
		super({
			...props,
		});

		const EMPTY_PATHS = STICKMAN_RIGGER.render([]);

		this.add(
			<Rect>
				{range(EMPTY_PATHS.length).map(i => {
					return <Path
						data={() => this.pathsInfo()[i].data}
						stroke={EMPTY_PATHS[i].stroke}
						fill={EMPTY_PATHS[i].fill}
						lineWidth={EMPTY_PATHS[i].lineWidth}
						lineCap={EMPTY_PATHS[i].lineCap}
						position={() => [this.size().x / -2, this.size().y / -2]}
					/>
				})}
			</Rect>
		);
	}
}