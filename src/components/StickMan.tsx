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
import { CoolGradient } from '../utils/CoolGradient';

import { NumpyData, PoseInfo, StemInfo } from '../generated/DataClasses';

enum BoneGroup {
	ARM = "Arm",
	LEG = "Leg",
	TORSO = "Torso",
	HEAD = "Head"
}

// This is if we're just lookin at it. So this is refersed from the perspective of the person
enum BoneSide {
	RIGHT = "Right",
	LEFT = "Left",
	CENTER = "Center"
}

const ENABLE_BODY_COLORS = false;
class BoneInfo {
	start_index: number;
	end_index: number;
	color: string;
	group: BoneGroup;
	side: BoneSide;
	sub_order: number;

	constructor(start_index: number, end_index: number, color: string, group: BoneGroup, side: BoneSide, sub_order: number = 0) {
		this.start_index = start_index;
		this.end_index = end_index;
		this.color = color;
		this.group = group;
		this.side = side;
		this.sub_order = sub_order;
	}

	toSvgCommand(points: Vector2[]) {
		var xy1 = `${points[this.start_index].x.toFixed(2)},${points[this.start_index].y.toFixed(2)}`;
		var xy2 = `${points[this.end_index].x.toFixed(2)},${points[this.end_index].y.toFixed(2)}`;
		return `M ${xy1} L ${xy2}`
	}

	getColor() {
		if (ENABLE_BODY_COLORS) {
			if (this.group == BoneGroup.TORSO || this.group == BoneGroup.HEAD) {
				return "#212630";
			}
			else if (this.group == BoneGroup.ARM || this.group == BoneGroup.LEG) {
				if (this.sub_order == 0) {
					return "#2c323f"
				}
				return "#2e3542"
			}
		}
		return this.color;
	}
}


class FingerInfo {
	indices: number[];
	color: string;

	constructor(indices: number[], color: string) {
		this.indices = indices;
		this.color = color;
	}

	toSvgCommand(points: Vector2[]) {
		var xy_list = this.indices.map(i => `${points[i].x.toFixed(2)},${points[i].y.toFixed(2)}`);
		var result = `M ${xy_list[0]}`;
		for (var i = 1; i < xy_list.length; i++) {
			result += ` L ${xy_list[i]}`;
		}
		return result;
	}
}

function drawSvgLoop(points: Vector2[]) {
	var xy_list = points.map(p => `${p.x.toFixed(2)},${p.y.toFixed(2)}`);
	var result = `M ${xy_list[0]}`;
	for (var i = 1; i < xy_list.length; i++) {
		result += ` L ${xy_list[i]}`;
	}
	result += " Z";
	return result;
}

class BodyInfo {
	finger_infos: FingerInfo[];
	bones: BoneInfo[];

	constructor(finger_infos: FingerInfo[], bones: BoneInfo[]) {
		this.finger_infos = finger_infos;
		this.bones = bones;
	}

	toPaths(body_points: Vector2[], left_hand_points: Vector2[], right_hand_points: Vector2[], size: Vector2) {
		var path_stuff: object[] = [];
		var torso_bones = this.bones.filter(b => b.group == BoneGroup.TORSO);
		var pre_torso_points = torso_bones.map(b => [ b.start_index, b.end_index ]);
		pre_torso_points = [[5], [12], [9], [2]];
		var torso_points = Array.from(new Set(pre_torso_points.flat())).map(i => body_points[i]);
		if (ENABLE_BODY_COLORS) {
			path_stuff.push({
				data: drawSvgLoop(torso_points),
				fill: torso_bones[torso_bones.length - 1].getColor(),
			});
		}
		this.bones.forEach(bone => {
			path_stuff.push({
				data: bone.toSvgCommand(body_points),
				lineWidth: 20,
				color: bone.getColor()
			});

			if (bone.group == BoneGroup.ARM && bone.sub_order == 1) {
				var finger_points = bone.side == BoneSide.LEFT ? left_hand_points : right_hand_points;
				if (finger_points.length > 0) {
					this.finger_infos.forEach(finger => {
						path_stuff.push({
							data: finger.toSvgCommand(finger_points),
							lineWidth: 8,
							color: finger.color
						});
					})
				}
			}
		});

		return path_stuff.map(p => {
			return <Path
				stroke={p.color}
				lineWidth={p.lineWidth}
				lineCap={"round"}
				fill={p.fill}
				data={p.data}
				position={[size.x / -2, size.y / -2]}
			></Path>;
		});
	}
}

// for each finger, the indexes of that finger in order
const FINGERS = [
	new FingerInfo([ 0, 17, 18, 19, 20 ], "#0051cb"),
	new FingerInfo([ 0, 13, 14, 15, 16 ], "#00cc50"),
	new FingerInfo([ 0, 9, 10, 11, 12 ], "#a2cc00"),
	new FingerInfo([ 0, 5, 6, 7, 8 ], "#b10000"),
	new FingerInfo([ 0, 1, 2, 3, 4 ], "#a200cb"), // thumb
];

const BONES_BODY25 = [
	// torso
	new BoneInfo(8, 9, "#009933", BoneGroup.TORSO, BoneSide.LEFT),
	new BoneInfo(8, 12, "#006699", BoneGroup.TORSO, BoneSide.RIGHT),
	new BoneInfo(1, 2, "#983200", BoneGroup.TORSO, BoneSide.LEFT),
	new BoneInfo(1, 5, "#669900", BoneGroup.TORSO, BoneSide.RIGHT),
	new BoneInfo(1, 8, "#980000", BoneGroup.TORSO, BoneSide.CENTER),

	// head
	new BoneInfo(1, 0, "#a20036", BoneGroup.HEAD, BoneSide.CENTER),

	// legs
	new BoneInfo(9, 10, "#009664", BoneGroup.LEG, BoneSide.LEFT, 0),
	new BoneInfo(10, 11, "#009797", BoneGroup.LEG, BoneSide.LEFT, 1),
	new BoneInfo(12, 13, "#003399", BoneGroup.LEG, BoneSide.RIGHT, 0),
	new BoneInfo(13, 14, "#000099", BoneGroup.LEG, BoneSide.RIGHT, 1),

	// arms
	new BoneInfo(2, 3, "#956400", BoneGroup.ARM, BoneSide.LEFT, 0),
	new BoneInfo(3, 4, "#989800", BoneGroup.ARM, BoneSide.LEFT, 1),
	new BoneInfo(5, 6, "#319700", BoneGroup.ARM, BoneSide.RIGHT, 0),
	new BoneInfo(6, 7, "#009600", BoneGroup.ARM, BoneSide.RIGHT, 1),
];
const BONES_COCO = [
	// torso
	new BoneInfo(1, 8, "#009900", BoneGroup.TORSO, BoneSide.LEFT),
	new BoneInfo(1, 11, "#009999", BoneGroup.TORSO, BoneSide.RIGHT),
	new BoneInfo(1, 2, "#983200", BoneGroup.TORSO, BoneSide.LEFT),
	new BoneInfo(1, 5, "#669900", BoneGroup.TORSO, BoneSide.RIGHT),

	// head
	new BoneInfo(1, 0, "#000099", BoneGroup.HEAD, BoneSide.CENTER),

	// legs
	new BoneInfo(8, 9, "#009933", BoneGroup.LEG, BoneSide.LEFT, 0),
	new BoneInfo(9, 10, "#009966", BoneGroup.LEG, BoneSide.LEFT, 1),
	new BoneInfo(11, 12, "#006699", BoneGroup.LEG, BoneSide.RIGHT, 0),
	new BoneInfo(12, 13, "#003399", BoneGroup.LEG, BoneSide.RIGHT, 1),

	// arms
	new BoneInfo(2, 3, "#956400", BoneGroup.ARM, BoneSide.LEFT, 0),
	new BoneInfo(3, 4, "#989800", BoneGroup.ARM, BoneSide.LEFT, 1),
	new BoneInfo(5, 6, "#319700", BoneGroup.ARM, BoneSide.RIGHT, 0),
	new BoneInfo(6, 7, "#009600", BoneGroup.ARM, BoneSide.RIGHT, 1),
];

const BONES = BONES_BODY25;

const BODY_INFO = new BodyInfo(FINGERS, BONES);

// Function to calculate the angle between two vectors
function angleBetween(v1: Vector2, v2: Vector2) {
	let dotProduct = v1.x * v2.x + v1.y * v2.y;
	let magnitudeV1 = Math.sqrt(v1.x * v1.x + v1.y * v1.y);
	let magnitudeV2 = Math.sqrt(v2.x * v2.x + v2.y * v2.y);
	return Math.acos(dotProduct / (magnitudeV1 * magnitudeV2));
}

function isInner(a: Vector2, b: Vector2, c: Vector2) {
	return ((b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)) > 0;
}

// get the angle on the right side of the line that is created by connecting a to b to c
function getAngleOnRight(a: Vector2, b: Vector2, c: Vector2) {
	let ba = new Vector2({ x: a.x - b.x, y: a.y - b.y });
	let bc = new Vector2({ x: c.x - b.x, y: c.y - b.y });

	let angle = angleBetween(ba, bc);
	if (isInner(a, b, c)) {
		angle = (2 * Math.PI) - angle;
	}
	return angle;
}

// returns a point c such that a->b->c form a straight line
function extendLine(a: Vector2, b: Vector2) {
	return new Vector2(
		(b.x - a.x)	+ b.x,
		(b.y - a.y)	+ b.y,
	);
}

function calculateOffsetPoint(a: Vector2, b: Vector2, c: Vector2, distance: number) {
	var is_straight = false;
	if (a.x == b.x && a.y == b.y) {
		a = extendLine(c, b);
		is_straight = true;
	}
	if (c.x == b.x && c.y == b.y) {
		c = extendLine(a, b);
		is_straight = true;
	}

	let o = new Vector2(b.x + 1, b.y); // a point that points toward radians origin from b

	// Calculate the angle between ba and bc
	let angle = is_straight ? 180 : getAngleOnRight(a, b, c);
	var origin_angle = getAngleOnRight(o, b, a);

	var final_angle = (angle / 2) + origin_angle;
	
	if (final_angle > (Math.PI * 2)) {
		final_angle -= (Math.PI * 2);
	}

	// Calculate new point d
	distance = 0 - distance;
	let d = {
		x: b.x + distance * Math.cos(final_angle),
		y: b.y + distance * Math.sin(final_angle)
	};

	return new Vector2(d);
}

class FrameInfo {
	body_d: string;
	head_position: Vector2;
	head_radius: number;

	constructor() {
		this.body_d = "";
		this.head_position = new Vector2(0, 0);
		this.head_radius = 1;
	}
}

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

	// frame info tryna make a drawn outline
	// private readonly frameInfo: SimpleSignal<FrameInfo> = createSignal(() => {
	// 	var pose_info = this.pose_info();
	// 	var frame = pose_info.DATA_poseframes.frameSignal();
	// 	var posedata = pose_info.DATA_poseframes.data;

	// 	var points: Vector2[] = [];
	// 	for (var i = 0; i < posedata.shape[1]; i += 3) {
	// 		points.push(new Vector2(posedata.get(frame, i), posedata.get(frame, i + 1)));
	// 	}
	// 	var man_outline = [ 5, 1, 2, 3, 4, 4, 3, 2, 9, 10, 11, 11, 10, 9, 12, 13, 14, 14, 13, 12, 5, 6, 7, 7, 6 ];

	// 	var outline_points1 = man_outline.map(i => points[i]);
	// 	var outline_points2 = man_outline.map((p_index, i) => {
	// 		var a = i == 0 ? man_outline.length - 1 : i - 1;
	// 		var b = i;
	// 		var c = i == man_outline.length - 1 ? 0 : i + 1;
	// 		return calculateOffsetPoint(points[man_outline[a]], points[man_outline[b]], points[man_outline[c]], 20);
	// 	});

	// 	// draw points
	// 	var commands = [];
	// 	for (var i = 0; i < outline_points2.length; i++) {
	// 		var cmd = "L";
	// 		if (i == 0) {
	// 			cmd = "M";
	// 		}
	// 		var pt = outline_points2[i];
	// 		commands.push(`${cmd} ${pt.x.toFixed(2)},${pt.y.toFixed(2)}`);
	// 	}
	// 	commands.push("Z");

	// 	// draw head circle
	// 	const dx = points[1].x - points[0].x;
	// 	const dy = points[1].y - points[0].y;
	// 	const distance = Math.sqrt(dx * dx + dy * dy);

	// 	var frameInfo = new FrameInfo();
	// 	frameInfo.body_d = commands.join(" ")
	// 	frameInfo.head_position = points[0];
	// 	frameInfo.head_radius = distance * 0.75;

	// 	return frameInfo;
	// });

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

	
	private readonly leftHandPoints: SimpleSignal<Vector2[]> = createSignal(() => {
		var pose_info = this.pose_info();
		var out_size = this.size();
		var frame = pose_info.DATA_pose.frameSignal();
		var hand_data = pose_info.DATA_hand_left.data;
		
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
		for (var i = 0; i < hand_data.shape[1]; i += 3) {
			points.push(new Vector2(
				points_offset.x + (hand_data.get(frame, i) * points_multiplier.x),
				points_offset.y + (hand_data.get(frame, i + 1) * points_multiplier.y)
			));
		}
		return points;
	});

	private readonly container = createRef<Rect>();
	private readonly path = createRef<Path>();

	

	public constructor(props?: StickManProps) {
		super({
			...props,
		});

		this.add(
			<Rect>
				{/* fill={"#ff0000"}
				size={() => this.size()}> */}

				{/* <Path
					stroke={"#000000"}
					lineWidth={4}
					ref={this.path}
					fill={"#ff0000"}
					data={() => this.frameInfo().body_d}
				></Path>
				<Circle
					stroke={"#000000"}
					lineWidth={4}
					fill={"#ff0000"}
					position={() => this.frameInfo().head_position}
					size={() => {
						var thing = this.frameInfo().head_radius / 2;
						return [thing, thing]
					}}
				></Circle> */}
				{/* {range(BONES.length).map(i => { // index 0 is at the top
					return <Path
						stroke={BONES[i].color}
						lineWidth={20}
						lineCap={"round"}
						data={() => BONES[i].toSvgCommand(this.framePoints())}
						position={() => [this.size().x / -2, this.size().y / -2]}
					></Path>
				})}
				{range(FINGERS.length).map(i => { // index 0 is at the top
					return <Path
						stroke={FINGERS[i].color}
						lineWidth={5}
						lineCap={"round"}
						data={() => FINGERS[i].toSvgCommand(this.leftHandPoints())}
						position={() => [this.size().x / -2, this.size().y / -2]}
					></Path>
				})} */}

				{() => BODY_INFO.toPaths(this.framePoints(), this.leftHandPoints(), this.leftHandPoints(), this.size())}
			</Rect>
		);
	}
}