import os
import struct

import numpy as np

import state


def calculate_new_weights(old_weights_path, new_weights_path, lr=1):
    """
    Calculate the new weights given the path to the old weights file. Also
    write the weights with the given the new weights path.

    Only called for iOS Library sessions for text data.
    
    Args:
        old_weights_path (str): Path to old weights file.
        new_weights_path (str): Path to write new weights.
        lr (int, optional): The learning rate of the model. Defaults to 1.
    
    Returns:
        list: A list of the calculated new weights, used for testing/debugging.
    """
    layers_bytes = []
    layers_data = {}

    def read_write(bytes_to_read, data_format=None):
        data = f_read.read(bytes_to_read)
        f_write.write(data)
        if data_format:
            return struct.unpack(data_format, data)
    
    with open(new_weights_path, "wb") as f_write:
        with open(old_weights_path, "rb") as f_read:
            layers_arr = read_write(4, "<i")
            num_layers = layers_arr[0]
            
            read_write(4) # padding bytes

            while len(layers_bytes) < num_layers:
                layer_bytes = read_write(16, "<iiii")
                layers_bytes.append(layer_bytes)

            weights = []
            layers_data = []
            
            for layer_num, _, num_bytes, _ in layers_bytes:
                data = struct.unpack("f" * int(num_bytes / 4), f_read.read(num_bytes))
                layers_data.append(data)

                if layer_num % 2 == 0:
                    continue

                if (layer_num + 1) % 4 == 0:
                    weights.append(data)
                    weights.append(bias)
                else:
                    bias = data

            old_weights = [np.array(weight) for weight in weights]
            new_weights = old_weights - lr * state.state["current_gradients"]

            for layer_data, layer_bytes in zip(layers_data, layers_bytes):
                layer_num, _, num_bytes, _ = layer_bytes
                if layer_num % 2 != 0:
                    if layer_num % 4 == 1:
                        layer_data = new_weights[int(layer_num/2) + 1] # bias
                    else:
                        layer_data = new_weights[int(layer_num/2) - 1] # kernel
                f_write.write(struct.pack("f" * int(num_bytes / 4), *layer_data))
    return new_weights

                
def read_compiled_weights(weights_path):
    """
    Read the weights at the given path.

    Worked off of: https://gist.github.com/ghop02/9b09dcf7c5ee73f5dce6ba0e7c6f41d0#file-_read_compiled_coreml_weights-py

    NOTE: Only used for testing, may possibly have use in the future.
    
    Args:
        weights_path (str): Path to the weights.
    
    Returns:
        list: A list of the calculated new weights, used for testing/debugging.
    """
    layer_bytes = []
    layer_data = {}
    with open(weights_path, "rb") as f:
        # First byte of the file is an integer with how many
        # sections there are.  This lets us iterate through each section
        # and get the map for how to read the rest of the file.
        num_layers = struct.unpack("<i", f.read(4))[0]

        f.read(4)  # padding bytes

        # The next section defines the number of bytes each layer contains.
        # It has a format of
        # | Layer Number | <padding> | Bytes in layer | <padding> |
        while len(layer_bytes) < num_layers:
            layer_num, _, num_bytes, _ = struct.unpack("<iiii", f.read(16))
            layer_bytes.append((layer_num, num_bytes))

        weights = []
        # Read actual layer weights.  Weights are floats as far as I can tell.
        for layer_num, num_bytes in layer_bytes:
            data = struct.unpack("f" * int(num_bytes / 4), f.read(num_bytes))
            if layer_num % 2 == 0:
                continue

            if (layer_num + 1) % 4 == 0:
                weights.append(data)
                weights.append(bias)
            else:
                bias = data

        return [np.array(weight) for weight in weights]
