"""
Models Module - Neural Network Architectures for PINN

This module contains neural network architectures used in the PINN
for PM2.5 dispersion modeling.
"""

import torch
import torch.nn as nn
import numpy as np


class SimpleMLP(nn.Module):
    """
    Simple Multi-Layer Perceptron for PINN.
    
    This is the basic architecture suitable for learning PDEs.
    Uses Tanh activation for smooth derivatives (important for autograd).
    """
    
    def __init__(self, input_dim, hidden_dims, output_dim=1):
        """
        Args:
            input_dim: Number of input features (e.g., 2 for x,t or 3 for x,y,t)
            hidden_dims: List of hidden layer sizes (e.g., [64, 64, 64])
            output_dim: Number of outputs (1 for concentration)
        """
        super().__init__()
        
        layers = []
        prev_dim = input_dim
        
        # Hidden layers
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.Tanh())  # Tanh is smooth - good for PDE derivatives
            prev_dim = hidden_dim
        
        # Output layer (no activation - we want unbounded concentration values)
        layers.append(nn.Linear(prev_dim, output_dim))
        
        self.network = nn.Sequential(*layers)
        
        # Initialize weights using Xavier initialization
        self._init_weights()
    
    def _init_weights(self):
        """Xavier initialization for better training stability."""
        for layer in self.network:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_normal_(layer.weight)
                nn.init.zeros_(layer.bias)
    
    def forward(self, x):
        """
        Forward pass.
        
        Args:
            x: Input tensor of shape (batch_size, input_dim)
        
        Returns:
            Output tensor of shape (batch_size, output_dim)
        """
        return self.network(x)


class PINN_1D(nn.Module):
    """
    1D Physics-Informed Neural Network.
    
    Specialized for 1D advection-diffusion: C(x, t)
    """
    
    def __init__(self, hidden_dims=[64, 64, 64, 64]):
        """
        Args:
            hidden_dims: List of hidden layer sizes
        """
        super().__init__()
        self.net = SimpleMLP(input_dim=2, hidden_dims=hidden_dims, output_dim=1)
    
    def forward(self, inputs):
        """
        Args:
            inputs: Tensor of shape (N, 2) where columns are [x, t]
                    OR can pass x and t separately
        
        Returns:
            Concentration C of shape (N, 1)
        """
        return self.net(inputs)


class PINN_2D(nn.Module):
    """
    2D Physics-Informed Neural Network.
    
    Specialized for 2D advection-diffusion: C(x, y, t)
    """
    
    def __init__(self, hidden_dims=[64, 64, 64, 64, 64, 64]):
        """
        Args:
            hidden_dims: List of hidden layer sizes (deeper for 2D)
        """
        super().__init__()
        self.net = SimpleMLP(input_dim=3, hidden_dims=hidden_dims, output_dim=1)
    
    def forward(self, inputs):
        """
        Args:
            inputs: Tensor of shape (N, 3) where columns are [x, y, t]
        
        Returns:
            Concentration C of shape (N, 1)
        """
        return self.net(inputs)


class FourierFeatureNetwork(nn.Module):
    """
    Neural network with Fourier feature encoding.
    
    Fourier features help overcome "spectral bias" - the tendency of 
    neural networks to learn low-frequency functions first. This is
    important for capturing sharp gradients in pollution fields.
    
    Reference: Tancik et al., "Fourier Features Let Networks Learn 
    High Frequency Functions in Low Dimensional Domains" (2020)
    """
    
    def __init__(self, input_dim, hidden_dims, output_dim=1, 
                 num_frequencies=64, frequency_scale=1.0):
        """
        Args:
            input_dim: Original input dimension
            hidden_dims: List of hidden layer sizes
            output_dim: Output dimension
            num_frequencies: Number of Fourier frequencies
            frequency_scale: Scale factor for frequencies
        """
        super().__init__()
        
        self.input_dim = input_dim
        self.num_frequencies = num_frequencies
        
        # Random Fourier feature matrix (fixed, not learned)
        B = torch.randn(input_dim, num_frequencies) * frequency_scale
        self.register_buffer('B', B)
        
        # Network takes encoded features as input
        encoded_dim = 2 * num_frequencies  # sin and cos for each frequency
        self.net = SimpleMLP(encoded_dim, hidden_dims, output_dim)
    
    def encode(self, x):
        """Apply Fourier feature encoding."""
        # x shape: (batch, input_dim)
        # B shape: (input_dim, num_frequencies)
        proj = torch.matmul(x, self.B)  # (batch, num_frequencies)
        return torch.cat([torch.sin(2 * np.pi * proj), 
                         torch.cos(2 * np.pi * proj)], dim=-1)
    
    def forward(self, x):
        encoded = self.encode(x)
        return self.net(encoded)


# ============================================================
# EXAMPLE USAGE
# ============================================================
if __name__ == "__main__":
    print("Testing neural network architectures...\n")
    
    # Test 1D PINN
    print("1. Testing PINN_1D:")
    model_1d = PINN_1D(hidden_dims=[32, 32, 32])
    x = torch.rand(10, 1)  # 10 spatial points
    t = torch.rand(10, 1)  # 10 time points
    inputs = torch.cat([x, t], dim=-1)
    output = model_1d(inputs)
    print(f"   Input shape: {inputs.shape}")
    print(f"   Output shape: {output.shape}")
    print(f"   ✅ 1D PINN working!\n")
    
    # Test 2D PINN
    print("2. Testing PINN_2D:")
    model_2d = PINN_2D(hidden_dims=[64, 64, 64, 64])
    x = torch.rand(10, 1)
    y = torch.rand(10, 1)
    t = torch.rand(10, 1)
    inputs = torch.cat([x, y, t], dim=-1)
    output = model_2d(inputs)
    print(f"   Input shape: {inputs.shape}")
    print(f"   Output shape: {output.shape}")
    print(f"   ✅ 2D PINN working!\n")
    
    # Count parameters
    total_params_1d = sum(p.numel() for p in model_1d.parameters())
    total_params_2d = sum(p.numel() for p in model_2d.parameters())
    print(f"Model sizes:")
    print(f"   1D PINN: {total_params_1d:,} parameters")
    print(f"   2D PINN: {total_params_2d:,} parameters")
