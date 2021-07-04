import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import kerastuner as kt
import pickle

# Loads dataset
dataset_train = pickle.load(open("dataset_train.p", "rb"))
dataset_test = pickle.load(open("dataset_test.p", "rb"))

class Sampling(layers.Layer):
    """Sampling layer that samples from latent space"""
    def call(self, inputs):
        z_mean, z_log_var = inputs
        batch = tf.shape(z_mean)[0]
        dim = tf.shape(z_mean)[1]

        epsilon = tf.keras.backend.random_normal(shape=(batch, dim))
        return z_mean + tf.exp(0.5 * z_log_var) * epsilon


class VAE(keras.Model):
    """
    VAE model definition

    Takes the encoder, decoder as inputs, as well as the beta parameter.
    """
    
    def __init__(self, encoder, decoder, beta, **kwargs):
        super(VAE, self).__init__(**kwargs)
        self.beta = beta
        self.encoder = encoder
        self.decoder = decoder
        self.total_loss_tracker = keras.metrics.Mean(name="total_loss")
        self.reconstruction_loss_tracker = keras.metrics.Mean(
            name="reconstruction_loss"
        )
        self.kl_loss_tracker = keras.metrics.Mean(name="kl_loss")

        self.f_loss_trackers = {
          "recycling": keras.metrics.Mean(name = "recycling_loss"),
          "mobility": keras.metrics.Mean(name = "mobility_loss"),
          "diet": keras.metrics.Mean(name = "diet_loss"),
          "co2": keras.metrics.Mean(name = "co2_loss")
        }

    @property
    def metrics(self):
        return [
            self.total_loss_tracker,
            self.reconstruction_loss_tracker,
            self.kl_loss_tracker,
            self.f_loss_trackers["recycling"],
            self.f_loss_trackers["mobility"],
            self.f_loss_trackers["diet"],
            self.f_loss_trackers["co2"]
        ]

    def train_step(self, data):
        """Defines the training step"""

        with tf.GradientTape() as tape:
            z_mean, z_log_var, z = self.encoder(data)
            reconstruction = self.decoder(z)

            # Binary cross-entropy loss for recycling preferences
            recycling_loss = tf.reduce_mean(
                 keras.losses.binary_crossentropy(
                    data[:,:,0:5],
                    reconstruction[:,:,0:5]
                    ),
                    axis = 1
            )

            # MSE loss for mobility
            mobility_loss = tf.reduce_mean(
                    keras.losses.mean_squared_error(data[:,:,5:9], reconstruction[:,:,5:9]),
		axis = 1
	    )

            # Categorical cross-entropy loss for Co2 votes
            co2_loss = tf.reduce_mean(
                    keras.losses.categorical_crossentropy(
                    data[:,:,9:13],
                    reconstruction[:,:,9:13]
                    ),
                    axis = 1
		) 

            # MSE loss for diet preferences
            mse = keras.losses.mean_squared_error(data[:,:,13], reconstruction[:,:,13])
            diet_loss = tf.reduce_mean(
                    tf.reduce_sum(
                    mse
                    )
	    )

            reconstruction_loss = recycling_loss + diet_loss + mobility_loss + co2_loss

            kl_loss = -0.5 * (1 + z_log_var - tf.square(z_mean) - tf.exp(z_log_var))
            kl_loss = self.beta * tf.reduce_mean(tf.reduce_sum(kl_loss, axis=1))
            total_loss = reconstruction_loss + kl_loss

        grads = tape.gradient(total_loss, self.trainable_weights)
        self.optimizer.apply_gradients(zip(grads, self.trainable_weights))
        self.total_loss_tracker.update_state(total_loss)
        self.reconstruction_loss_tracker.update_state(reconstruction_loss)
        self.kl_loss_tracker.update_state(kl_loss)

        # Updates loss trackers for feature categories
        self.f_loss_trackers["recycling"].update_state(recycling_loss)
        self.f_loss_trackers["mobility"].update_state(mobility_loss)
        self.f_loss_trackers["diet"].update_state(diet_loss)
        self.f_loss_trackers["co2"].update_state(diet_loss)

        return {
            "loss": self.total_loss_tracker.result(),
            "f_recycling_loss": self.f_loss_trackers["recycling"].result(),
            "f_mobility_loss": self.f_loss_trackers["mobility"].result(),
            "f_diet_loss": self.f_loss_trackers["diet"].result(),
            "f_co2_loss": self.f_loss_trackers["co2"].result(),
            "reconstruction_loss": self.reconstruction_loss_tracker.result(),
            "kl_loss": self.kl_loss_tracker.result(),
        }


    def test_step(self, data):
        """Defines the test on the validation set"""
        if isinstance(data, tuple):
            data = data[0]

        z_mean, z_log_var, z = self.encoder(data)
        reconstruction = self.decoder(z)

        # Binary cross-entropy loss for recycling preferences
        recycling_loss = tf.reduce_mean(
             keras.losses.binary_crossentropy(
                data[:,:,0:5],
                reconstruction[:,:,0:5]
                ),
                axis = 1
        )

        # MSE loss for mobility
        mobility_loss = tf.reduce_mean(
                keras.losses.mean_squared_error(data[:,:,5:9], reconstruction[:,:,5:9]),
	axis = 1
	)

        # Categorical cross-entropy loss for Co2 votes
        co2_loss = tf.reduce_mean(
                keras.losses.categorical_crossentropy(
                data[:,:,9:13],
                reconstruction[:,:,9:13]
                ),
                axis = 1
	) 

        # MSE loss for diet preferences
        mse = keras.losses.mean_squared_error(data[:,:,13], reconstruction[:,:,13])
        diet_loss = tf.reduce_mean(
                tf.reduce_sum(
                mse
                )
	)

        reconstruction_loss = tf.reduce_mean(recycling_loss + diet_loss + mobility_loss + co2_loss)

        kl_loss = -0.5 * (1 + z_log_var - tf.square(z_mean) - tf.exp(z_log_var))
        kl_loss = self.beta * tf.reduce_mean(tf.reduce_sum(kl_loss, axis=1))
        total_loss = reconstruction_loss + kl_loss

        return {
            "loss": total_loss,
            "reconstruction_loss": reconstruction_loss,
            "kl_loss": kl_loss
        }

def model_builder(hp):
    """Builds the VAE model with hyperparameters"""
    latent_dim = hp.Choice('latent_dim', [1,2,3,4], default = 2)
    beta = hp.Choice('beta', [1,2,3,5,10])
    learning_rate = hp.Choice('learning_rate', values=[1e-2, 1e-3, 1e-4])
    kernel_size = hp.Choice('kernel_size', [1,3,5], default = 3)
    second_conv = hp.Choice('second_conv', [0, 16, 32, 64])
    
    # Encoder part

    encoder_inputs = keras.Input(shape=(128, 16))
    x = layers.Conv1D(16, kernel_size, activation="relu", padding="causal")(encoder_inputs)

    # Adds optional second convolutional layer
    if second_conv:
        x = layers.Conv1D(second_conv, kernel_size, activation="relu", padding="causal")(x)

    x = layers.Flatten()(x)
    z_mean = layers.Dense(latent_dim, name="z_mean")(x)
    z_log_var = layers.Dense(latent_dim, name="z_log_var")(x)
    z = Sampling()([z_mean, z_log_var])
    encoder = keras.Model(encoder_inputs, [z_mean, z_log_var, z], name="encoder")
    encoder.summary()

    # Decoder part
    
    latent_inputs = keras.Input(shape=(latent_dim,))
    x = layers.Dense(2048, activation="relu")(latent_inputs)
    x = layers.Reshape((128, 16))(x)

    # Adds optional second deconvolutional layer
    if second_conv:
        x = layers.Conv1DTranspose(second_conv, kernel_size, activation="relu", padding="same")(x)

    decoder_outputs = layers.Conv1DTranspose(16, kernel_size, activation="sigmoid", padding="same")(x)
    decoder = keras.Model(latent_inputs, decoder_outputs, name="decoder")
    decoder.summary()


    # Defines the model, compiles, and returns it
    vae = VAE(encoder, decoder, beta)
    vae.compile(loss = None, optimizer=keras.optimizers.Adam(learning_rate = learning_rate))
    return vae

# Initializes hyperband tuner
tuner = kt.Hyperband(model_builder,
                     objective='val_loss',
                     max_epochs=20,
                     factor=3,
                     seed=42,
                     directory='hypersearch',
                     project_name='vae')

# Print search space summary
print(tuner.search_space_summary())

# Starts hyperparameter search
tuner.search(dataset_train, epochs=20, batch_size = 64, validation_data = (dataset_train, dataset_train))

# Prints hyperparameter search results
print(tuner.results_summary())
