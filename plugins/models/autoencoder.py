import keras
from keras.layers import *
from keras.models import Model, Sequential
from keras.optimizers import Adam

from deepprofiler.learning.model import DeepProfilerModel


def define_model(config, dset):
    input_shape = (
        config["sampling"]["box_size"],  # height
        config["sampling"]["box_size"],  # width
        len(config["image_set"]["channels"])  # channels
    )
    input_image = keras.layers.Input(input_shape)

    if config['model']['conv_blocks'] < 1:
        raise ValueError("At least 1 convolutional block is required.")

    x = input_image
    for i in range(config['model']['conv_blocks']):
        x = Conv2D(8 * 2 ** i, (3, 3), activation='relu', padding='same')(x)
        x = MaxPooling2D((2, 2), padding='same')(x)
    encoded = x
    encoded_shape = encoded._keras_shape[1:]
    encoder = Model(input_image, encoded)

    decoder_input = Input(encoded_shape)
    decoder_layers = []
    for i in reversed(range(config['model']['conv_blocks'])):
        decoder_layers.extend([
            Conv2DTranspose(8 * 2 ** i, (3, 3), activation='relu', padding='same'),
            UpSampling2D((2, 2))
        ])
    decoder_layers.append(Conv2DTranspose(len(config["image_set"]["channels"]), (3, 3), activation='sigmoid', padding='same'))
    decoder = Sequential(decoder_layers, name='decoded')
    decoded = decoder(encoded)
    decoder = Model(decoder_input, decoder(decoder_input))

    autoencoder = Model(input_image, decoded)
    autoencoder.compile(optimizer=Adam(lr=config['training']['learning_rate']), loss='mse')

    return autoencoder, encoder, decoder


class ModelClass(DeepProfilerModel):
    def __init__(self, config, dset, generator):
        super(ModelClass, self).__init__(config, dset, generator)
        self.model, self.encoder, self.decoder = define_model(config, dset)
