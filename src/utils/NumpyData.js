import npyjs from 'npyjs';
import ndarray from 'ndarray';

console.time("NumpyData load");

const n = new npyjs();

var response = await n.load("src/generated/data.npy");

var data = ndarray(response.data, response.shape);

console.timeEnd("NumpyData load");
 
export const NUMPY_DATA = data;

/*
// TODO: implement this much more broad export
stuff to export here:
- frame count
- freqData
	- a list/dict? of these, one for each "instrument"?
	- also want one for all instruments together "original"?
- json info about the song
	- song name THIS IS USED TO FIND THE DATA FILES ETC
	- key
	- bpm
	- list of the instrument names

// OK NEXT 2 BIG STEPS
// - see if we can do a toSignal() on the numpy data we get (tho make sure to support stripping whitespace)
// - rewrite the python generator code to create the json file and have good support for creating the other stuff
*/