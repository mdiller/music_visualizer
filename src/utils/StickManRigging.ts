import { Vector2 } from "@motion-canvas/core";
import * as svgtools from '../utils/svgtools';


export enum StickManModel {
	BONES = "Bones",
	BLUEGUY = "Blueguy",
}

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
		if (points.length == 0) {
			return "";
		}
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
		if (points.length == 0) {
			return "";
		}
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

	toPaths(body_points: Vector2[], left_hand_points: Vector2[], right_hand_points: Vector2[]) {
		var paths: svgtools.PathInfo[] = [];
		var torso_bones = this.bones.filter(b => b.group == BoneGroup.TORSO);
		var pre_torso_points = torso_bones.map(b => [ b.start_index, b.end_index ]);
		pre_torso_points = [[5], [12], [9], [2]];
		var torso_points = Array.from(new Set(pre_torso_points.flat())).map(i => body_points[i]);
		if (ENABLE_BODY_COLORS) {
			paths.push(new svgtools.PathInfo({
				data: drawSvgLoop(torso_points),
				lineCap: "round",
				fill: torso_bones[torso_bones.length - 1].getColor(),
			}));
		}
		this.bones.forEach(bone => {
			paths.push(new svgtools.PathInfo({
				data: bone.toSvgCommand(body_points),
				lineWidth: 20,
				lineCap: "round",
				stroke: bone.getColor()
			}));

			if (bone.group == BoneGroup.ARM && bone.sub_order == 1) {
				var finger_points = bone.side == BoneSide.LEFT ? left_hand_points : right_hand_points;
				if (finger_points.length > 0) {
					this.finger_infos.forEach(finger => {
						paths.push(new svgtools.PathInfo({
							data: finger.toSvgCommand(finger_points),
							lineWidth: 8,
							lineCap: "round",
							stroke: finger.color
						}));
					})
				}
			}
		});

		return paths;
	}
	toPathsv2(body_points: Vector2[], left_hand_points: Vector2[], right_hand_points: Vector2[]) {
		var points = body_points;
		var man_outline = [ 5, 1, 2, 3, 4, 4, 3, 2, 9, 10, 11, 11, 10, 9, 12, 13, 14, 14, 13, 12, 5, 6, 7, 7, 6 ];
		var commands = [];
		if (body_points.length > 0) {
			var outline_points2 = man_outline.map((p_index, i) => {
				var a = i == 0 ? man_outline.length - 1 : i - 1;
				var b = i;
				var c = i == man_outline.length - 1 ? 0 : i + 1;
				return svgtools.calculateOffsetPoint(points[man_outline[a]], points[man_outline[b]], points[man_outline[c]], 20);
			});
			
			outline_points2.forEach((point, i) => {
				if (i == 0) {
					commands.push(`M${point.x},${point.y}`);
					return;
				}
				if (i < 2 || i > outline_points2.length - 2) {
					commands.push(`L ${point.x.toFixed(2)},${point.y.toFixed(2)}`);
				}
				else {
					commands.push(svgtools.bezierCommand(point, i, outline_points2));
				}
			});
			commands.push("Z");
		}

		return [ new svgtools.PathInfo({
			stroke: "#28b0de",
			lineWidth: 5,
			lineCap: "round",
			fill: "#daf7f5",
			data: commands.join(" ")
		}) ];
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

export class StickManRigger {
	model: StickManModel;
	body: BodyInfo;

	constructor(model: StickManModel) {
		this.model = model;
		this.body = new BodyInfo(FINGERS, BONES);
	}

	render(body_points: Vector2[]) {
		if (this.model == StickManModel.BONES) {
			return this.body.toPaths(body_points, [], []);
		}
		else if (this.model == StickManModel.BLUEGUY) {
			return this.body.toPathsv2(body_points, [], []);
		}
	}
}

