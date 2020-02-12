class DataConfig(object):
    def __init__(self, data_type, class_labels):
        self.data_type = data_type
        self.class_labels = class_labels

    def serialize(self):
        return {
            "data_type": self.data_type,
            "class_labels": self.class_labels,
        }

class ImageConfig(DataConfig):
    def __init__(self, class_labels, color_space, dims):
        super.__init__("image", class_labels)
        self.color_space = color_space
        self.dims = dims

    def serialize(self):
        config = super.serialize()
        image_config = {
            "color_space": self.color_space,
            "dims": self.dims
        }
        config["image_config"] = image_config
        return config
    