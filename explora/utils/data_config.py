class DataConfig(object):
    """
    Basic object that represent a data config. Not meant to initialized
    directly. Used strictly for starting iOS training sessions.
    
    Args:
        data_type (str): The type of data.
        class_labels (list): The list of possible labels in the dataset.
    """
    def __init__(self, data_type, class_labels):
        self.data_type = data_type
        self.class_labels = class_labels

    def __eq__(self, other):
        """
        Custom comparator for checking equality between data configs.
        
        Args:
            other (DataConfig): The other data config to compare with.
        
        Returns:
            bool: True if equal, False otherwise.
        """
        return self.data_type == other.data_type \
            and self.class_labels == other.class_labels

    def serialize(self):
        """
        Serialize the config into a dictionary.
        
        Returns:
            dict: The serialized data config.
        """
        return {
            "data_type": self.data_type,
            "class_labels": self.class_labels,
        }

class ImageConfig(DataConfig):
    """
    Basic object that represents a data config. Used strictly for starting iOS
    training sessions when dealing with an image dataset.
    
    Args:
        class_labels (list): The list of possible labels in the dataset.
        color_space (str): The type of image that is inputted into the model. 
            Must be either `GRAYSCALE` or `COLOR`.
        image_dims (tuple): The dimensions of image that is inputted into the 
            model. Must have a length of 2 (width x height).
    """
    def __init__(self, class_labels, color_space, dims):
        super().__init__("image", class_labels)
        self.color_space = color_space
        self.dims = dims

    def __eq__(self, other):
        """
        Custom comparator for checking equality between image configs.
        
        Args:
            other (ImageConfig): The other image config to compare with.
        
        Returns:
            bool: True if equal, False otherwise.
        """
        return super().__eq__(other) \
            and self.color_space == other.color_space \
            and self.dims == other.dims

    def serialize(self):
        """
        Serialize the config into a dictionary.
        
        Returns:
            dict: The serialized image config.
        """
        config = super().serialize()
        image_config = {
            "color_space": self.color_space,
            "dims": self.dims
        }
        config["image_config"] = image_config
        return config

class TextConfig(DataConfig):
    """
    Basic object that represents a data config. Used strictly for starting iOS
    training sessions when dealing with a text dataset.
    
    Args:
        vocab_size (int): The size of the vocab set.
    """
    def __init__(self, vocab_size):
        super().__init__("image", list(range(vocab_size + 1)))
    