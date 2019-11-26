from keras.models import load_model
import tensorflow as tf 
import tensorflowjs as tfjs
import keras

from keras import backend as K

# print(keras.__version__, 'keras')
# print(tf.__version__, "tf")
# print(tfjs.__version__, "tfjs")

tf.compat.v1.disable_eager_execution()

model = load_model('tools/assets/my_model.h5')

print(K.eval(model.optimizer.lr))

# tfjs.converters.save_keras_model(model, 'javascript')

