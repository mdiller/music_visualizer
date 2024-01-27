import { Vector2 } from "@motion-canvas/core";

// export Function to calculate the angle between two vectors
export function angleBetween(v1: Vector2, v2: Vector2) {
	let dotProduct = v1.x * v2.x + v1.y * v2.y;
	let magnitudeV1 = Math.sqrt(v1.x * v1.x + v1.y * v1.y);
	let magnitudeV2 = Math.sqrt(v2.x * v2.x + v2.y * v2.y);
	return Math.acos(dotProduct / (magnitudeV1 * magnitudeV2));
}

export function isInner(a: Vector2, b: Vector2, c: Vector2) {
	return ((b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)) > 0;
}

// get the angle on the right side of the line that is created by connecting a to b to c
export function getAngleOnRight(a: Vector2, b: Vector2, c: Vector2) {
	let ba = new Vector2({ x: a.x - b.x, y: a.y - b.y });
	let bc = new Vector2({ x: c.x - b.x, y: c.y - b.y });

	let angle = angleBetween(ba, bc);
	if (isInner(a, b, c)) {
		angle = (2 * Math.PI) - angle;
	}
	return angle;
}

// returns a point c such that a->b->c form a straight line
export function extendLine(a: Vector2, b: Vector2) {
	return new Vector2(
		(b.x - a.x)	+ b.x,
		(b.y - a.y)	+ b.y,
	);
}

export function calculateOffsetPoint(a: Vector2, b: Vector2, c: Vector2, distance: number) {
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



export function line(pointA: any, pointB: any) {
	const lengthX = pointB.x - pointA.x
	const lengthY = pointB.y - pointA.y
	
	return {
		length: Math.sqrt(Math.pow(lengthX, 2) + Math.pow(lengthY, 2)),
		angle: Math.atan2(lengthY, lengthX)
	}
}

export function controlPoint(current: any, previous: any, next: any, reverse = false) {  // When 'current' is the first or last point of the array
	// 'previous' or 'next' don't exist.
	// Replace with 'current'
	const p = previous || current
	const n = next || current  // The smoothing ratio
	if (n == undefined || p == undefined) {
		return current
	}
	const smoothing = 0.2  // Properties of the opposed-line
	const o = line(p, n)  // If is end-control-point, add PI to the angle to go backward
	const angle = o.angle + (reverse ? Math.PI : 0)
	const length = o.length * smoothing  // The control point position is relative to the current point
	const x = current.x + Math.cos(angle) * length
	const y = current.y + Math.sin(angle) * length
	
	return new Vector2(x, y)
  }

// Create the bezier curve command 
// I:  - point (array) [x,y]: current point coordinates
//     - i (integer): index of 'point' in the array 'a'
//     - a (array): complete array of points coordinates
// O:  - (string) 'C x2,y2 x1,y1 x,y': SVG cubic bezier C command
export function bezierCommand(point: any, i: any, a: any) {
	const pt1 = controlPoint(a[i - 1], a[i - 2], point);
	const pt2 = controlPoint(point, a[i - 1], a[i + 1], true);
	return ` C ${pt1.x},${pt2.y} ${pt2.x},${pt2.y} ${point.x},${point.y}`
}

type PathInfoJson = {
	data: string;
	stroke?: string;
	fill?: string;
	lineWidth?: number;
	lineCap?: CanvasLineCap;
}

export class PathInfo {
	data: string;
	stroke: string;
	fill: string;
	lineWidth: number;
	lineCap: CanvasLineCap;

	constructor(json: PathInfoJson) {
		this.data = json.data;
		this.stroke = json.stroke;
		this.fill = json.fill;
		this.lineWidth = json.lineWidth;
		this.lineCap = json.lineCap;
	}
}
