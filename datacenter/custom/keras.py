"""
Custom saving/loading for Keras.
Based on https://github.com/keras-team/keras/blob/master/keras/engine/saving.py.
"""

import json

from keras import optimizers

from keras.models import model_from_json


def model_from_serialized(serialized_model):
    uncompiled_model = model_from_json(serialized_model['architecture'])
    return _load_optimizer(uncompiled_model, serialized_model['optimizer'])

def get_optimizer(model):
    def get_json_type(obj):
        """Serialize any object to a JSON-serializable structure.
        # Arguments
            obj: the object to serialize
        # Returns
            JSON-serializable structure representing `obj`.
        # Raises
            TypeError: if `obj` cannot be serialized.
        """
        # if obj is a serializable Keras class instance
        # e.g. optimizer, layer
        if hasattr(obj, 'get_config'):
            return {'class_name': obj.__class__.__name__,
                    'config': obj.get_config()}

        # if obj is any numpy type
        if type(obj).__module__ == np.__name__:
            if isinstance(obj, np.ndarray):
                return {'type': type(obj),
                        'value': obj.tolist()}
            else:
                return obj.item()

        # misc functions (e.g. loss function)
        if callable(obj):
            return obj.__name__

        # if obj is a python 'type'
        if type(obj).__name__ == type.__name__:
            return obj.__name__

        raise TypeError('Not JSON Serializable:', obj)

    if model.optimizer:
        metadata = {}
        if isinstance(model.optimizer, optimizers.TFOptimizer):
            warnings.warn(
                'TensorFlow optimizers do not '
                'make it possible to access '
                'optimizer attributes or optimizer state '
                'after instantiation. '
                'As a result, we cannot save the optimizer '
                'as part of the model save file.'
                'You will have to compile your model again '
                'after loading it. '
                'Prefer using a Keras optimizer instead '
                '(see keras.io/optimizers).')
        else:
            metadata['training_config'] = json.dumps({
                'optimizer_config': {
                    'class_name': model.optimizer.__class__.__name__,
                    'config': model.optimizer.get_config()
                },
                'loss': model.loss,
                'metrics': model.metrics,
                'sample_weight_mode': model.sample_weight_mode,
                'loss_weights': model.loss_weights,
            }, default=get_json_type)

    return metadata

def _load_optimizer(uncompiled_model, optimizer_metadata):
    custom_objects = {}

    def convert_custom_objects(obj):
        """Handles custom object lookup.
        # Arguments
            obj: object, dict, or list.
        # Returns
            The same structure, where occurrences
                of a custom object name have been replaced
                with the custom object.
        """
        if isinstance(obj, list):
            deserialized = []
            for value in obj:
                deserialized.append(convert_custom_objects(value))
            return deserialized
        if isinstance(obj, dict):
            deserialized = {}
            for key, value in obj.items():
                deserialized[key] = convert_custom_objects(value)
            return deserialized
        if obj in custom_objects:
            return custom_objects[obj]
        return obj

    # instantiate optimizer
    training_config = optimizer_metadata.get('training_config')
    if training_config is None:
        warnings.warn('No training configuration found in save file: '
                      'the model was *not* compiled. '
                      'Compile it manually.')
        return uncompiled_model
    training_config = json.loads(training_config)
    optimizer_config = training_config['optimizer_config']
    optimizer = optimizers.deserialize(optimizer_config,
                                       custom_objects=custom_objects)

    # Recover loss functions and metrics.
    loss = convert_custom_objects(training_config['loss'])
    metrics = convert_custom_objects(training_config['metrics'])
    sample_weight_mode = training_config['sample_weight_mode']
    loss_weights = training_config['loss_weights']

    # Compile model.
    uncompiled_model.compile(optimizer=optimizer,
                             loss=loss,
                             metrics=metrics,
                             loss_weights=loss_weights,
                             sample_weight_mode=sample_weight_mode)

    model = uncompiled_model
    return model
