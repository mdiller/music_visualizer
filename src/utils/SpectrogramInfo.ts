export class SpectrogramInfo {
    name: string;
    frame_count: number;
    framerate: number;
    octaves: number;
    bins_per_octave: number;
    min_x: number;
    max_x: number;
	data: any;

    constructor(json: { name: string; frame_count: number; framerate: number; octaves: number; bins_per_octave: number; min_x: number; max_x: number, data: any }) {
        this.name = json.name;
        this.frame_count = json.frame_count;
        this.framerate = json.framerate;
        this.octaves = json.octaves;
        this.bins_per_octave = json.bins_per_octave;
        this.min_x = json.min_x;
        this.max_x = json.max_x;
        this.data = json.data;
    }
}