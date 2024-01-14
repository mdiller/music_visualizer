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

import { NumpyData, PoseInfo, StemInfo } from '../generated/DataClasses';

const RAW_POSE = [
	157.175,
	47.417,
	0.886651,
	118.935,
	106.773,
	0.878091,
	73.6057,
	115.359,
	0.798794,
	61.3787,
	200.745,
	0.801116,
	89.2229,
	160.654,
	0.807009,
	169.368,
	104.973,
	0.786136,
	174.619,
	188.583,
	0.742659,
	185.082,
	151.97,
	0.822231,
	145.004,
	251.227,
	0.62697,
	115.394,
	252.955,
	0.596311,
	113.634,
	399.262,
	0.778871,
	103.129,
	533.27,
	0.780241,
	174.576,
	247.767,
	0.619748,
	186.757,
	407.883,
	0.819797,
	188.608,
	536.833,
	0.807005,
	145.065,
	35.3272,
	0.957224,
	160.631,
	37.0685,
	0.872322,
	115.448,
	45.7192,
	0.846671,
	0,
	0,
	0,
	164.166,
	569.825,
	0.670928,
	186.761,
	568.121,
	0.668134,
	198.928,
	548.998,
	0.67633,
	108.444,
	564.679,
	0.658724,
	92.7644,
	562.932,
	0.74627,
	99.74,
	538.544,
	0.525256
];

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

	private readonly data = createSignal(() => {
		var pose_info = this.pose_info();
		var frame = pose_info.DATA_poseframes.frameSignal();
		var posedata = pose_info.DATA_poseframes.data;

		var points: Vector2[] = [];
		for (var i = 0; i < posedata.shape[1]; i += 3) {
			points.push(new Vector2(posedata.get(frame, i), posedata.get(frame, i + 1)));
		}
		// var man_outline = [ 5, 5, 2, 9, 10, 11, 14, 13, 12 ];
		var man_outline = [ 5, 1, 2, 3, 4, 4, 3, 2, 9, 10, 11, 11, 10, 9, 12, 13, 14, 14, 13, 12, 5, 6, 7, 7, 6 ];

		// var man_outline = [ 5, 5, 2, 2, 3, 3, 4, 4, 3, 3, 2, 2, 9, 9, 10, 0, 11, 1, 10, 0, 9, 9, 12, 2, 13, 3, 14, 4, 13, 3, 12, 2, 5, 5, 6, 6, 7, 7, 6, 6 ];

		// var man_outline = [ 5, 5, 2,2, 9, 9, 12, 12 ];

		var outline_points1 = man_outline.map(i => points[i]);
		var outline_points2 = man_outline.map((p_index, i) => {
			var a = i == 0 ? man_outline.length - 1 : i - 1;
			var b = i;
			var c = i == man_outline.length - 1 ? 0 : i + 1;
			return calculateOffsetPoint(points[man_outline[a]], points[man_outline[b]], points[man_outline[c]], 10);
		});

		// draw points
		var commands2 = [];
		for (var i = 0; i < outline_points2.length; i++) {
			var cmd = "L";
			if (i == 0) {
				cmd = "M";
			}
			var pt = outline_points2[i];
			commands2.push(`${cmd} ${pt.x},${pt.y}`);
		}
		commands2.push("Z");
		var d = commands2.join(" ");

		return d;
	});

	private readonly container = createRef<Rect>();
	private readonly path = createRef<Path>();

	

	public constructor(props?: StickManProps) {
		super({
			...props,
		});
		// convert raw data to points
		// var points: Vector2[] = [];
		// for (var i = 0; i < RAW_POSE.length; i += 3) {
		// 	points.push(new Vector2(RAW_POSE[i], RAW_POSE[i + 1]));
		// }
		// console.log("start")
		// // var man_outline = [ 5, 5, 2, 9, 10, 11, 14, 13, 12 ];
		// var man_outline = [ 5, 1, 2, 3, 4, 4, 3, 2, 9, 10, 11, 11, 10, 9, 12, 13, 14, 14, 13, 12, 5, 6, 7, 7, 6 ];

		// // var man_outline = [ 5, 5, 2, 2, 3, 3, 4, 4, 3, 3, 2, 2, 9, 9, 10, 0, 11, 1, 10, 0, 9, 9, 12, 2, 13, 3, 14, 4, 13, 3, 12, 2, 5, 5, 6, 6, 7, 7, 6, 6 ];

		// // var man_outline = [ 5, 5, 2,2, 9, 9, 12, 12 ];

		// var outline_points1 = man_outline.map(i => points[i]);
		// var outline_points2 = man_outline.map((p_index, i) => {
		// 	var a = i == 0 ? man_outline.length - 1 : i - 1;
		// 	var b = i;
		// 	var c = i == man_outline.length - 1 ? 0 : i + 1;
		// 	return calculateOffsetPoint(points[man_outline[a]], points[man_outline[b]], points[man_outline[c]], 10);
		// });

		// console.log(outline_points2);
		
		// // outline_points1[0].x += 10;

		// // draw points
		// var commands = [];
		// for (var i = 0; i < outline_points1.length; i++) {
		// 	var cmd = "L";
		// 	if (i == 0) {
		// 		cmd = "M";
		// 	}
		// 	var pt = outline_points1[i];
		// 	commands.push(`${cmd} ${pt.x},${pt.y}`);
		// }
		// commands.push("Z");
		// var d = commands.join(" ");

		// // draw points
		// var commands2 = [];
		// for (var i = 0; i < outline_points2.length; i++) {
		// 	var cmd = "L";
		// 	if (i == 0) {
		// 		cmd = "M";
		// 	}
		// 	var pt = outline_points2[i];
		// 	commands2.push(`${cmd} ${pt.x},${pt.y}`);
		// }
		// commands2.push("Z");
		// var d2 = commands2.join(" ");

		// var d = "M0,0 L100,100 L200,0 Z";

		this.add(
			<Rect>
				<Path
					stroke={"#000000"}
					lineWidth={4}
					ref={this.path}
					fill={"#ff0000"}
					data={this.data}
				></Path>
				{/* <Path
					ref={this.path}
					fill={"#00ff00"}
					data={d}
					opacity={0.5}
				></Path> */}
			</Rect>
		);
	}
}