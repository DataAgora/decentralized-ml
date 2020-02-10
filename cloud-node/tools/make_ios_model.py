# def convert_keras_to_mlmodel(keras_url, mlmodel_url):
#     """This method simply converts the keras model to a mlmodel using coremltools.
#     keras_url - The URL the keras model will be loaded.
#     mlmodel_url - the URL the Core ML model will be saved.
#     """
#     from keras.models import load_model
#     keras_model = load_model(keras_url)
    
#     from coremltools.converters import keras as keras_converter
#     class_labels = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
#     mlmodel = keras_converter.convert(keras_model, input_names=['image'],
#                                 output_names=['output'],
#                                 class_labels=class_labels,
#                                 predicted_feature_name='label')
    
#     mlmodel.save(mlmodel_url)

# keras_model_path = 'assets/ios_model.h5'
# coreml_model_path = 'assets/temp_model.mlmodel'
# convert_keras_to_mlmodel(keras_model_path , coreml_model_path)

# import coremltools
# spec = coremltools.utils.load_spec(coreml_model_path)
# builder = coremltools.models.neural_network.NeuralNetworkBuilder(spec=spec)
# builder.inspect_layers()

# neuralnetwork_spec = builder.spec

# # change the input so the model can accept 28x28 grayscale images
# neuralnetwork_spec.description.input[0].type.imageType.width = 28
# neuralnetwork_spec.description.input[0].type.imageType.height = 28

# from coremltools.proto import FeatureTypes_pb2 as _FeatureTypes_pb2
# grayscale = _FeatureTypes_pb2.ImageFeatureType.ColorSpace.Value('GRAYSCALE')
# neuralnetwork_spec.description.input[0].type.imageType.colorSpace = grayscale

# def make_updatable(builder, mlmodel_url, mlmodel_updatable_path):
#     """This method makes an existing non-updatable mlmodel updatable.
#     mlmodel_url - the path the Core ML model is stored.
#     mlmodel_updatable_path - the path the updatable Core ML model will be saved.
#     """
#     import coremltools
#     model_spec = builder.spec

#     from keras.models import load_model
#     model = load_model(keras_model_path)
#     trainable_layer_names = [layer.name for layer in model.layers if layer.trainable]
#     print(trainable_layer_names)
#     trainable_layer_names = [layer.name for layer in model.layers if layer.get_weights()]
#     print(trainable_layer_names)
#     # make_updatable method is used to make a layer updatable. It requires a list of layer names.
#     # dense_1 and dense_2 are two innerProduct layer in this example and we make them updatable.
#     builder.make_updatable(trainable_layer_names)

#     # Categorical Cross Entropy or Mean Squared Error can be chosen for the loss layer.
#     # Categorical Cross Entropy is used on this example. CCE requires two inputs: 'name' and 'input'.
#     # name must be a string and will be the name associated with the loss layer
#     # input must be the output of a softmax layer in the case of CCE. 
#     # The loss's target will be provided automatically as a part of the model's training inputs.
#     builder.set_categorical_cross_entropy_loss(name='lossLayer', input='output')

#     from keras import backend as K
#     lr = K.eval(model.optimizer.lr)
#     print(lr)
#     # in addition of the loss layer, an optimizer must also be defined. SGD and Adam optimizers are supported.
#     # SGD has been used for this example. To use SGD, one must set lr(learningRate) and batch(miniBatchSize) (momentum is an optional parameter).
#     from coremltools.models.neural_network import SgdParams
#     builder.set_sgd_optimizer(SgdParams(lr=lr, batch=4))

#     # Finally, the number of epochs must be set as follows.
#     builder.set_epochs(3)

#     # save the updated spec
#     from coremltools.models import MLModel
#     mlmodel_updatable = MLModel(model_spec)
#     mlmodel_updatable.save(mlmodel_updatable_path)

# coreml_updatable_model_path = 'assets/my_model.mlmodel'
# make_updatable(builder, coreml_model_path, coreml_updatable_model_path)

from keras.models import load_model
# import keras
# from keras.models import Sequential
# from keras.layers import Dense, Dropout, Flatten, Conv2D, MaxPooling2D
# model = load_model('assets/ios_model.h5')
# model.summary()
# layer_weight_shapes = {}
# for i, layer in enumerate(model.layers):
#     layer_weight_shapes[i] = []
#     weights = layer.get_weights()
#     if len(weights) == 2:
#         #print(weights[0].shape)
#         print(weights[1])
#         print(len(weights[1]))
#     layer_weight_shapes[i] = [weight.shape for weight in weights]
# print(layer_weight_shapes)

# model = Sequential()
# model.add(Dense(8, input_shape=(8,), bias_initializer='ones'))
# model.compile(loss=keras.losses.categorical_crossentropy,
#                   optimizer=keras.optimizers.SGD(lr=0.01),
#                   metrics=['accuracy'])
# model.summary()
# from coremltools.converters import keras as keras_converter
# ml_model = keras_converter.convert(model)
# ml_model.save('test3.mlmodel')
# model.save('simple_model3.h5')
# print(model.get_weights())

# model = Sequential()
# model.add(Dense(8, input_shape=(8,), bias_initializer='ones'))
# model.compile(loss=keras.losses.categorical_crossentropy,
#                   optimizer=keras.optimizers.SGD(lr=0.01),
#                   metrics=['accuracy'])
# model.summary()
# from coremltools.converters import keras as keras_converter
# ml_model = keras_converter.convert(model)
# ml_model.save('test4.mlmodel')
# model.save('simple_model4.h5')
# print(model.get_weights())

model = load_model("assets/ios_model.h5")
print(model.get_weights())
print(len(model.get_weights()))
# for layer in model.layers:
#     print(layer.get_weights())