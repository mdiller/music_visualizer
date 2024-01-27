import numpy as np
	
def rolling_average(data: np.ndarray, window_size: float) -> np.ndarray:
	original_size = len(data)
	data = np.convolve(data, np.ones(window_size), 'valid') / window_size
	pad_size = original_size - len(data)
	if pad_size > 0:
		last_value = data[-1]
		data = np.pad(data, (0, pad_size), 'constant', constant_values=last_value)
	return data

def rolling_average2d(data: np.ndarray, window_size: float) -> np.ndarray:
	shape = (data.shape[0] - window_size + 1, window_size, data.shape[1])
	strides = (data.strides[0], data.strides[0], data.strides[1])
	sliding_windows = np.lib.stride_tricks.as_strided(data, shape=shape, strides=strides)
	return sliding_windows.mean(axis=1)

def apply_decay(data: np.ndarray, decay_factor: float) -> np.ndarray:
	# Iterate through the rows (previously columns in C)
	for i in range(1, data.shape[0]):
		for j in range(data.shape[1]):
			# Apply decay if the current value is lower than the decayed previous value
			data[i, j] = max(data[i, j], data[i-1, j] * decay_factor)
	return data