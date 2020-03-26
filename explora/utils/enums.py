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
    TEXT = "text"

class ModelNames(Enum):
    MNIST = "mnist"
    NGRAM = "n-gram"

class ModelPaths(Enum):
    """
    Enum to enumerate the paths of the default models.
    """
    MNIST_PATH = "artifacts/init_mlp_model_with_w.h5"
    IOS_MNIST_PATH = "artifacts/small_ios_model.h5"
    NGRAM_PATH = "artifacts/neural_ngram_updatable.mlmodel"

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
    INVALID_KERAS_MODEL_PATH = "Invalid Keras model path! Check that the " \
        "file exists and is a `.h5` file!"
    INVALID_MLMODEL_PATH = "Invalid `MLModel` model path! Check that the " \
        "file exists and is a `.mlmodel` file!"
    NOT_COMPILED = "Model must compiled with optimizer and loss!"
    INVALID_LOSS = "Loss must be categorical cross entropy or mean squared " \
        "error for iOS library!"
    INVALID_OPTIMIZER = "Optimizer must be SGD or Adam for iOS library!"
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
    SET_DATA_CONFIG = "Data config should not be set for non iOS libraries!"
    INVALID_DATA_TYPE = "Invalid data type! The only valid data types are: " \
        "{}".format(data_types)
    INVALID_CLASS_LABELS = "Class labels must be nonempty list!"
    INVALID_COLOR_SPACE = "Invalid color space! The only valid color spaces " \
        "are: {}".format(color_spaces) 
    INVALID_IMAGE_DIMS = "Image dimensions must be a tuple of 2 integers."
    MISSING_DATASET_ID = "Dataset ID must be string and is required for iOS " \
        "libraries!"
    SET_DATASET_ID = "Dataset ID should not be set for non iOS libraries!"
    INVALID_VOCAB_SIZE = "Vocab size must be int and greater than 0!"
    ONLY_MODEL_NAME_OR_PATH = "Only one of model path and model name must " \
        "be set!"
    UNKNOWN_MODEL_NAME = "Unknown model name provided for this library/data " \
        "type!"
    