import npyjs from 'npyjs';
import ndarray from 'ndarray';

console.time("NumpyData load");

const n = new npyjs();

var response = await n.load("src/generated/data.npy");

var data = ndarray(response.data, response.shape);

console.timeEnd("NumpyData load");
 
export const NUMPY_DATA = data;
