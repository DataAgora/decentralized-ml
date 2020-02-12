from enum import Enum


class LibraryType(Enum):
    """
    Enum to enumerate types of libraries.
    """
    PYTHON = "PYTHON"
    JAVASCRIPT = "JAVASCRIPT"
    IOS = "IOS"

class ColorSpace(Enum):
    """
    Enum to enumerate types of color spaces for image data for iOS training
    sessions.
    """
    GRAYSCALE = "GRAYSCALE"
    COLOR = "COLOR"

class DataType(Enum):
    """
    Enum to enumerate types of data for iOS training sessions.
    """
    IMAGE = "image"

library_types = tuple([library_type.value for library_type in LibraryType])
color_spaces = tuple([color_space.value for color_space in ColorSpace])
data_types = tuple([data_type.value for data_type in DataType])

class ErrorMessages(Enum):
    """
    Enum to enumerate the possible validation error messages.
    """
    INVALID_REPO_ID = "Repo ID is in an invalid format!"
    INVALID_LIBRARY_TYPE = "Invalid library type! The only valid library " \
        "types are: {}".format(library_types)    
    INVALID_MODEL_TYPE = "Provided model is not a Keras model!"
    NOT_COMPILED = "Model must compiled with optimizer and loss!"
    INVALID_LOSS = "Loss must be categorical cross entropy for iOS library!"
    INVALID_HYPERPARAMS = "Hyperparameters must include positive batch size!"
    INVALID_PERCENTAGE_AVERAGED = "Percentage averaged must be 1 OR float " \
        "and between 0 and 1!"
    INVALID_MAX_ROUNDS = "Max rounds must be int and at least 1!"
    INVALID_CHECKPOINT_FREQUENCY = "Checkpoint frequency must be int and " \
        "between 0 and max rounds!"
    DATA_CONFIG_NOT_SPECIFIED = "Data config must be specified for iOS " \
        "library!"
    UNKNOWN_CONFIG = "Unknown data config received! Use `make_data_config` " \
        "to generate the data config!"
    INVALID_DATA_TYPE = "Invalid data type! The only valid data types are: " \
        "{}".format(data_types)
    INVALID_CLASS_LABELS = "Class labels must be nonempty list!"
    INVALID_COLOR_SPACE = "Invalid color space! The only valid color spaces " \
        "are: {}".format(color_spaces) 
    INVALID_IMAGE_DIMS = "Image dimensions must be a tuple of 2 integers."