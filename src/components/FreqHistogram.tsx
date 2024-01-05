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
import NpyReader from '../utils/NpyReader'
import { COLOR_GRADIENTS } from '../generated/generated';
import { NUMPY_DATA } from '../utils/NumpyData'
// import NUMPY_RAW from '../generated/data.npy?raw'

export interface FreqHistogramProps extends NodeProps {
	frame: SignalValue<number>;
	size: SignalValue<Vector2>;
	strip?: SignalValue<boolean>;
}

export class FreqHistogram extends Node {
	@signal()
	public declare readonly frame: SimpleSignal<number, this>;
	
	@signal()
	public declare readonly size: SimpleSignal<Vector2, this>;
	
	@initial(false)
	@signal()
	public declare readonly strip: SimpleSignal<boolean, this>;

	private readonly container = createRef<Rect>();
	private readonly path = createRef<Path>();
	// private readonly data = createSignal(() => SVG_PATHS[this.frame()]);
	private readonly npyReader = new NpyReader("src/generated/data.npy");
	// private readonly svgWidth = createSignal(0);
	// private readonly svgHeight = createSignal(0);
	private readonly data = createSignal(() => this.npyReader.getFrameSvg(this.frame(), this.size().x, this.size().y));
	// private readonly data = createSignal(() => "");

	public constructor(props?: FreqHistogramProps) {
		super({
			...props,
		});

		// console.log(this.strip());
		console.log(NUMPY_DATA);

		// const thingie = createSignal(() => );
		// this.npyReader.getFrameSvg(this.frame(), 0, 0).then(thing => {
		// 	console.log(thing);
		// })
		const gradient = new Gradient({
			type: 'linear',
			// fromY: () => map(-300, 200, progress()),
			// toY: () => map(-200, 300, progress()),
			fromX: this.size().x,
			toX: this.size().y,
			stops: [
				{offset: 0, color: '#00ff00'},
				{offset: 1, color: '#ff0000'}
			]
			// stops: COLOR_GRADIENTS[0].colors.map(color => {
			// 	return {
			// 		offset: color.percent
			// 	}
			// }),
		  });

		this.add(
			<Path
				ref={this.path}
				fill={gradient}
				data={() => this.data()}
			></Path>
		);
		// <Rect
		// 	ref={this.container}
		// 	// fill="#00ff00"
		// 	width={"100%"}
		// 	height={"100%"}
		// 	direction="column"
		// 	justifyContent="end"
		// 	alignItems="center" layout>
		// 		<Path
		// 		ref={this.path}
		// 		fill={gradient}
		// 		data={() => this.data()}
		// 		></Path>
		// 	</Rect>


		// this.svgWidth(this.container().width());
		// this.svgHeight(this.container().height());
		// temp().width(this.container().width() / 6);
		// temp().height(this.container().height() / 6);
	}
}