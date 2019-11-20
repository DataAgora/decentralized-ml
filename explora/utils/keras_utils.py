import base64

import keras


def get_h5_model(model):
    """
    Saves a Keras model as an .h5 file and then reads the file as a string
    so that it can be transmitted to the server via WebSocket
    Args:
       model (keras.engine.Model): The model to be converted
    Returns:
        str: A string that represents the Keras model
    """
    model.save("core/model/my_model.h5")
    with open("core/model/my_model.h5", mode='rb') as file:
        file_content = file.read()
        encoded_content = base64.b64encode(file_content)
        h5_model = encoded_content.decode('ascii')
        return h5_model