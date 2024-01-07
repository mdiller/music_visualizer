import { Gradient } from "@motion-canvas/2d";
import { SpectrogramInfo } from "./SpectrogramInfo";


interface ColorStep {
	color: string;
	offset: number;
}

export class CoolGradient {
	stops: ColorStep[];
	isOctave: boolean;

	constructor(stops: ColorStep[], isOctave: boolean = false) {
		this.stops = stops;
		this.isOctave = isOctave;
	}
	
	static fromColors(colors: string[], isOctave: boolean = false): CoolGradient {
		return new CoolGradient(colors.map((color, i) => {
			return {
				color: color,
				offset: (i / (colors.length - 1))
			};
		}), isOctave);
	}

	static fromScale(rootColor: string, onScaleColor: string, offScaleColor: string): CoolGradient {
		let noteThickness: number = 0.5;

		// VERIFY that this adds up to 12 mebb?
		let majorScaleSteps: number[] = [1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1];
		let minorScaleSteps: number[] = [1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1];

		// F Major
		let scaleSteps: number[] = majorScaleSteps;
		let keyRootOffset: number = 8; // how many half-steps up from A is the root of the key (F => 8)

		let stepsPerOctave: number = scaleSteps.length; // should be 12


		let colors: ColorStep[] = [];
		for (let i: number = 0; i < stepsPerOctave; i++) {
			let color: string = scaleSteps[i] ? onScaleColor : offScaleColor;
			if (i === 0) {
				color = rootColor;
			}

			if (noteThickness === 0) {
				colors.push({
					color: color,
					offset: i / stepsPerOctave
				});
			} else {
				colors.push({
					color: color,
					offset: (i + (noteThickness / 2)) / stepsPerOctave
				});
				colors.push({
					color: color,
					offset: (i - (noteThickness / 2)) / stepsPerOctave
				});
			}
		}

		for (let color of colors) {
			let offset: number = color.offset;
			if (keyRootOffset !== 0) {
				offset += keyRootOffset / stepsPerOctave;
			}
			while (offset < 0) {
				offset += 1;
			}
			while (offset > 1) {
				offset -= 1;
			}
			color.offset = offset;
		}

		colors = colors.sort((a, b) => a.offset - b.offset);

		return new CoolGradient(colors, true);
	}

	toGradient(width: number, spectrogram: SpectrogramInfo): Gradient {
		if (!this.isOctave) {
			return new Gradient({
				type: 'linear',
				fromX: 0,
				toX: width,
				stops: this.stops
			});
		}
		var total_bins = spectrogram.octaves * spectrogram.bins_per_octave;

		var octave_start = spectrogram.min_x / spectrogram.bins_per_octave;
		var octave_end = spectrogram.octaves - ((total_bins - spectrogram.max_x) / spectrogram.bins_per_octave);

		var stops: ColorStep[] = [];
		for (var i = 0; i < spectrogram.octaves; i++) {
			this.stops.forEach(stop => {
				var octave_offset = i + stop.offset;
				if (octave_offset >= octave_start && octave_offset <= octave_end) {
					var percent_offset = (octave_offset - octave_start) / (octave_end - octave_start);
					stops.push({
						color: stop.color,
						offset: percent_offset
					})
				}
			})
		}

		// make sure we have a start and end
		if (stops[0].offset != 0) {
			stops.unshift({
				color: stops[0].color,
				offset: 0
			})
		}
		if (stops[stops.length - 1].offset != 1) {
			stops.push({
				color: stops[stops.length - 1].color,
				offset: 1
			})
		}

		return new Gradient({
			type: 'linear',
			fromX: 0,
			toX: width,
			stops: stops
		});
	}
}
