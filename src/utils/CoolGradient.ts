import { Gradient } from "@motion-canvas/2d";
import { StemInfo } from "../generated/DataClasses";


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
		let keyRootOffset: number = 5; // how many half-steps up from A is the root of the key (F => 8) (D => 5)

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

	toGradient(width: number, stem_info: StemInfo): Gradient {
		if (!this.isOctave) {
			return new Gradient({
				type: 'linear',
				fromX: 0,
				toX: width,
				stops: this.stops
			});
		}
		var total_bins = stem_info.octaves * stem_info.bins_per_octave;

		var octave_start = stem_info.min_x / stem_info.bins_per_octave;
		var octave_end = stem_info.octaves - ((total_bins - stem_info.max_x) / stem_info.bins_per_octave);

		var stops: ColorStep[] = [];
		for (var i = 0; i < stem_info.octaves; i++) {
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
	
	getColorAt(percent: number): string {
        // Ensure the input is between 0 and 1
        percent = Math.max(0, Math.min(1, percent));

        // Handle edge cases
        if (this.stops.length === 0) {
            throw new Error("Gradient has no color stops");
        }
        if (this.stops.length === 1 || percent <= this.stops[0].offset) {
            return this.stops[0].color;
        }
        if (percent >= this.stops[this.stops.length - 1].offset) {
            return this.stops[this.stops.length - 1].color;
        }

        // Find the two stops between which the percentage falls
        let startStop = this.stops[0];
        let endStop = this.stops[this.stops.length - 1];
        for (let i = 0; i < this.stops.length - 1; i++) {
            if (percent >= this.stops[i].offset && percent <= this.stops[i + 1].offset) {
                startStop = this.stops[i];
                endStop = this.stops[i + 1];
                break;
            }
        }

        // Calculate the relative position of the percentage between the two stops
        const range = endStop.offset - startStop.offset;
        const localPercent = (percent - startStop.offset) / range;

        // Interpolate the color
        return this.interpolateColor(startStop.color, endStop.color, localPercent);
    }

    private interpolateColor(color1: string, color2: string, percent: number): string {
        // Convert hex colors to RGB
        const [r1, g1, b1] = this.hexToRgb(color1);
        const [r2, g2, b2] = this.hexToRgb(color2);

        // Calculate the interpolated color
        const r = Math.round(r1 + (r2 - r1) * percent);
        const g = Math.round(g1 + (g2 - g1) * percent);
        const b = Math.round(b1 + (b2 - b1) * percent);

        // Convert back to hex and return
        return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
    }

    private hexToRgb(hex: string): [number, number, number] {
        // Expand shorthand form (e.g. "03F") to full form (e.g. "0033FF")
        const shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
        hex = hex.replace(shorthandRegex, (m, r, g, b) => r + r + g + g + b + b);

        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? [
            parseInt(result[1], 16),
            parseInt(result[2], 16),
            parseInt(result[3], 16)
        ] : [0, 0, 0];
    }
}
