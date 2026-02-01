# Configuration Files

This folder contains YAML configuration files for experiments.

Example structure:
```yaml
# experiment_01.yaml
model:
  type: PINN_1D
  hidden_dims: [64, 64, 64, 64]
  activation: tanh

training:
  epochs: 10000
  learning_rate: 0.001
  batch_size: 1000
  
physics:
  equation: advection_diffusion
  diffusion_coeff: 0.1
  advection_velocity: 1.0

data:
  x_range: [0, 1]
  t_range: [0, 1]
  n_collocation: 5000
```
