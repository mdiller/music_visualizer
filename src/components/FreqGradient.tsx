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
} from '@motion-canvas/core';
import { CoolGradient } from '../utils/CoolGradient';

import { NumpyData, StemInfo } from '../generated/DataClasses';

function line(pointA: any, pointB: any) {
	const lengthX = pointB[0] - pointA[0]
	const lengthY = pointB[1] - pointA[1]
	
	return {
		length: Math.sqrt(Math.pow(lengthX, 2) + Math.pow(lengthY, 2)),
		angle: Math.atan2(lengthY, lengthX)
	}
}

function controlPoint(current: any, previous: any, next: any, reverse = false) {  // When 'current' is the first or last point of the array
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
	const x = current[0] + Math.cos(angle) * length
	const y = current[1] + Math.sin(angle) * length
	
	return [x, y]
  }

// Create the bezier curve command 
// I:  - point (array) [x,y]: current point coordinates
//     - i (integer): index of 'point' in the array 'a'
//     - a (array): complete array of points coordinates
// O:  - (string) 'C x2,y2 x1,y1 x,y': SVG cubic bezier C command
function bezierCommand(point: any, i: any, a: any) {
	const pt1 = controlPoint(a[i - 1], a[i - 2], point);
	const pt2 = controlPoint(point, a[i - 1], a[i + 1], true);
	return ` C ${pt1[0]},${pt2[1]} ${pt2[0]},${pt2[1]} ${point[0]},${point[1]}`
}

function createPathData(stem_info: StemInfo, spectrogram: NumpyData, frame: number, width: number, height: number, include_end: boolean = true): string {
	var data = spectrogram.data;
	var frameLength = data.shape[1];
	var x_range = stem_info.max_x - stem_info.min_x
	var xMultiplier = width / x_range;
	var x_floor = stem_info.min_x;
	
	let d = `M0,${height}`;

	let lastXValue = 0;
	let points = [];
	for (var i = stem_info.min_x; i < stem_info.max_x; i++) {
		let yValue = height - Math.floor(data.get(frame, i) * height);
		let xValue = Math.floor((i - x_floor) * xMultiplier)
		if (yValue < 0) {
			yValue = 0;
		}
		if (yValue > 0) {
			lastXValue = xValue;
		}
		points.push([xValue, yValue]);
		//d += ` L${xValue},${yValue}`;
	}
	points.forEach((point, i) => {
		if (i > 0 && point[1] == height && points[i - 1][1] == height) {
			d+= ` M${point[0]},${point[1]}`;
			return;
		}
		
		if (true && (i > 5 && i < points.length - 5)) {
			d += bezierCommand(point, i, points);
		}
		else {
			d += ` L${point[0]},${point[1]}`;
		}
	});


	d += `L${lastXValue},${height}`;
	if (include_end) {
		d += 'Z';
	}

	return d;
}

export interface FreqGradientProps extends NodeProps {
	stem: SignalValue<StemInfo>;
	gradient?: SignalValue<CoolGradient>;
	size: SignalValue<Vector2>;
}

export class FreqGradient extends Node {
	@signal()
	public declare readonly stem: SimpleSignal<StemInfo, this>;

	@initial(CoolGradient.fromColors([ "#0e49be", "#ab08d2" ]))
	@signal()
	public declare readonly gradient: SimpleSignal<CoolGradient, this>;
	
	@signal()
	public declare readonly size: SimpleSignal<Vector2, this>;

	private readonly container = createRef<Rect>();
	private readonly path_blur = createRef<Path>();
	private readonly path_line = createRef<Path>();
	private readonly root_node = createRef<Node>();
	// TODO: make this into a "computed" method
	private readonly data = createSignal(() => createPathData(this.stem(), this.stem().DATA_spectrogram, this.stem().DATA_spectrogram.frameSignal(), this.size().x, this.size().y));
	private readonly dataDecayed = createSignal(() => createPathData(this.stem(), this.stem().DATA_spectrogram_decayed, this.stem().DATA_spectrogram_decayed.frameSignal(), this.size().x, this.size().y));
	private readonly dataNoWrap = createSignal(() => createPathData(this.stem(), this.stem().DATA_spectrogram, this.stem().DATA_spectrogram.frameSignal(), this.size().x, this.size().y, true));

	private readonly actualGradient = createSignal(() => {
		var stem = this.stem();
		var spectrogram = stem.DATA_spectrogram_decayed;
		var width = this.size().width;
		var frame = spectrogram.frameSignal();
		var gradient = this.gradient();

		var data = spectrogram.data;
		var frameLength = data.shape[1];
		var x_range = stem.max_x - stem.min_x
		var xMultiplier = 1 / x_range;
		var x_floor = stem.min_x;

		var stops: GradientStop[] = [];

		var zero_color = gradient.getColorAt(0);

		stops.push({
			offset: 0,
			color: zero_color
		});

		var just_wrote_0 = true;

		for (var i = stem.min_x; i < stem.max_x; i++) {
			let xValue = (i - x_floor) * xMultiplier;
			let yValue = data.get(frame, i);

			if (yValue > 0.05) {
				stops.push({
					offset: xValue,
					color: gradient.getColorAt(yValue)
				});
				just_wrote_0 = false;
			}
			else if (!just_wrote_0) {
				stops.push({
					offset: xValue,
					color: zero_color
				});
				just_wrote_0 = true;
			}
		}

		stops.push({
			offset: 1,
			color: zero_color
		});

		stops.forEach(stop => {
			console.log(stop.offset, stop.color.hex())
		})

		console.log(stops);

		return new Gradient({
			type: 'linear',
			fromX: 0,
			toX: width,
			stops: stops
		});
	})

	public constructor(props?: FreqGradientProps) {
		super({
			...props,
		});

		const back_opacity = 1;

		this.add(
			<Rect
				fill={this.actualGradient}
				size={this.size}
				x={() => this.size().width / 2}
				y={() => this.size().height / 2}
			/>
		);
	}
}