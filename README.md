# VAE model

This is the accompanying code to the thesis report "Deep Generative Modelling For Population Synthesis in Participatory Climate Simulations".

Similar to Jupyter notebooks, the code follows a literate programming approach. The .org files can be opened and executed in Emacs' [org-mode](https://orgmode.org/).

- `preparation.org`: Contains the data preprocessing and feature engineering code. The output is saved as "pickled" Python data structures.
- `vae4.org`: Contains the code for the baseline VAE model and code blocks to plot the latent space and the visualize the neural network architecture.
- `vae5_hyper.org`: Contains the code for the hyperparameter search.
- `epa_ghg_calculator.py`: Contains a modified version of the EPA carbon emissions calculator, and was provided by the external partner. The function `calculate_co2` is my own addition, with default values taken from the provided code.
- `sample.org`: Contains code blocks to sample from the VAE and generate plots for each feature category, marginal distributions and histograms for the GHG emissions distribution.

## Dependencies

The following Python packages were used.

```
matplotlib
pandas
numpy
tensorflow
scipy
pydot
statsmodels
scikit-learn
pymongo
keras-tuner
```

The .nix files provide a reproducible environment using the [Nix package manager](https://nixos.org/guides/install-nix.html).
