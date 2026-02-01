# Kandy PM2.5 Dispersion Modeling with Physics-Informed Neural Networks

A Physics-Informed Neural Network (PINN) approach to model PM2.5 dispersion in Kandy, Sri Lanka's topographically confined airshed.

## Project Overview

This undergraduate research project develops a transfer learning PINN that:
- Pre-trains on Salt Lake City, Utah data (abundant sensors + HRRR wind fields)
- Fine-tunes on sparse Kandy observations
- Embeds the advection-diffusion equation as a physics constraint
- Enables spatial reconstruction from minimal sensors (3-5 vs 24 required for traditional ML)

## The Physics

The advection-diffusion equation governing PM2.5 transport:

```
∂C/∂t + u·∇C = ∇·(K∇C) + S - R
```

Where:
- C(x,y,t) = PM2.5 concentration (μg/m³)
- u(x,y,t) = Wind velocity vector field (m/s)
- K = Turbulent diffusion coefficient (m²/s)
- S = Source term (emissions)
- R = Sink term (deposition)

## Project Structure

```
kandy_pm_pinn/
├── notebooks/           # Jupyter notebooks for exploration & learning
│   ├── 00_environment_test.ipynb
│   ├── 01_pytorch_basics.ipynb
│   └── ...
├── src/                 # Reusable Python modules
│   ├── __init__.py
│   ├── models.py        # Neural network architectures
│   ├── physics.py       # PDE residual computations
│   └── data.py          # Data loading utilities
├── data/                # Data files (gitignored if large)
├── configs/             # Experiment configurations
├── results/             # Output figures and analysis
├── requirements.txt     # Python dependencies
└── README.md
```

## Setup

```bash
# Create conda environment
conda create -n pinn python=3.10
conda activate pinn

# Install dependencies
pip install -r requirements.txt
```

## Progress Log

- [ ] Environment setup
- [ ] PyTorch/autograd fundamentals
- [ ] First 1D PINN (heat equation)
- [ ] 2D advection-diffusion PINN
- [ ] Salt Lake City data acquisition
- [ ] Pre-training on SLC
- [ ] Kandy data acquisition
- [ ] Transfer learning implementation
- [ ] Source identification (inverse problem)
- [ ] Documentation & thesis writing

## References

1. Bowatte et al. (2025) - RF-CNN pipeline for PM2.5 prediction in Sri Lanka
2. Senarathna et al. (2024) - PM2.5 patterns in Kandy
3. Raissi et al. (2019) - Physics-informed neural networks
4. Lu et al. (2021) - DeepXDE library

## Author

Daminda - Department of Environmental Sciences, University of Peradeniya

## License

MIT License - See LICENSE file for details
