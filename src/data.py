"""
Data Module - Data Loading and Preprocessing Utilities

This module contains functions for:
- Loading and processing sensor data (PurpleAir)
- Loading wind field data (HRRR, ERA5)
- Creating training datasets for PINN
- Generating collocation points
"""

import torch
import numpy as np
from typing import Tuple, Dict, Optional


def generate_collocation_points_1d(x_range: Tuple[float, float],
                                    t_range: Tuple[float, float],
                                    n_points: int = 1000,
                                    method: str = 'random') -> Dict[str, torch.Tensor]:
    """
    Generate collocation points for 1D PINN training.
    
    Collocation points are where we evaluate the physics residual.
    The PDE should be satisfied at these interior points.
    
    Args:
        x_range: (x_min, x_max) spatial domain
        t_range: (t_min, t_max) temporal domain
        n_points: Number of collocation points
        method: 'random' or 'grid'
    
    Returns:
        Dict with 'x' and 't' tensors, each of shape (n_points,)
    """
    x_min, x_max = x_range
    t_min, t_max = t_range
    
    if method == 'random':
        x = torch.rand(n_points) * (x_max - x_min) + x_min
        t = torch.rand(n_points) * (t_max - t_min) + t_min
    else:  # grid
        n_x = int(np.sqrt(n_points))
        n_t = n_points // n_x
        x_grid = torch.linspace(x_min, x_max, n_x)
        t_grid = torch.linspace(t_min, t_max, n_t)
        x, t = torch.meshgrid(x_grid, t_grid, indexing='ij')
        x = x.flatten()
        t = t.flatten()
    
    return {'x': x, 't': t}


def generate_collocation_points_2d(x_range: Tuple[float, float],
                                    y_range: Tuple[float, float],
                                    t_range: Tuple[float, float],
                                    n_points: int = 5000,
                                    method: str = 'random') -> Dict[str, torch.Tensor]:
    """
    Generate collocation points for 2D PINN training.
    
    Args:
        x_range: (x_min, x_max) spatial domain
        y_range: (y_min, y_max) spatial domain
        t_range: (t_min, t_max) temporal domain
        n_points: Number of collocation points
        method: 'random' or 'latin_hypercube'
    
    Returns:
        Dict with 'x', 'y', and 't' tensors
    """
    x_min, x_max = x_range
    y_min, y_max = y_range
    t_min, t_max = t_range
    
    if method == 'random':
        x = torch.rand(n_points) * (x_max - x_min) + x_min
        y = torch.rand(n_points) * (y_max - y_min) + y_min
        t = torch.rand(n_points) * (t_max - t_min) + t_min
    elif method == 'latin_hypercube':
        # Latin Hypercube Sampling for better coverage
        from scipy.stats import qmc
        sampler = qmc.LatinHypercube(d=3)
        sample = sampler.random(n=n_points)
        x = torch.tensor(sample[:, 0] * (x_max - x_min) + x_min, dtype=torch.float32)
        y = torch.tensor(sample[:, 1] * (y_max - y_min) + y_min, dtype=torch.float32)
        t = torch.tensor(sample[:, 2] * (t_max - t_min) + t_min, dtype=torch.float32)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return {'x': x, 'y': y, 't': t}


def generate_boundary_points_1d(x_range: Tuple[float, float],
                                 t_range: Tuple[float, float],
                                 n_points: int = 100) -> Dict[str, torch.Tensor]:
    """
    Generate boundary points for 1D problem.
    
    Boundaries are:
    - Left boundary: x = x_min for all t
    - Right boundary: x = x_max for all t
    - Initial condition: t = t_min for all x
    
    Args:
        x_range: (x_min, x_max)
        t_range: (t_min, t_max)
        n_points: Points per boundary
    
    Returns:
        Dict with boundary point information
    """
    x_min, x_max = x_range
    t_min, t_max = t_range
    
    t_boundary = torch.linspace(t_min, t_max, n_points)
    x_initial = torch.linspace(x_min, x_max, n_points)
    
    return {
        'left': {
            'x': torch.full((n_points,), x_min),
            't': t_boundary
        },
        'right': {
            'x': torch.full((n_points,), x_max),
            't': t_boundary
        },
        'initial': {
            'x': x_initial,
            't': torch.full((n_points,), t_min)
        }
    }


def normalize_data(data: torch.Tensor, 
                   method: str = 'minmax') -> Tuple[torch.Tensor, Dict]:
    """
    Normalize data for neural network training.
    
    Args:
        data: Input tensor
        method: 'minmax' (to [0,1]) or 'standard' (mean=0, std=1)
    
    Returns:
        Normalized data and normalization parameters for inverse transform
    """
    if method == 'minmax':
        data_min = data.min()
        data_max = data.max()
        normalized = (data - data_min) / (data_max - data_min + 1e-8)
        params = {'min': data_min, 'max': data_max, 'method': 'minmax'}
    elif method == 'standard':
        mean = data.mean()
        std = data.std()
        normalized = (data - mean) / (std + 1e-8)
        params = {'mean': mean, 'std': std, 'method': 'standard'}
    else:
        raise ValueError(f"Unknown normalization method: {method}")
    
    return normalized, params


def denormalize_data(data: torch.Tensor, params: Dict) -> torch.Tensor:
    """
    Reverse normalization to get original scale.
    
    Args:
        data: Normalized tensor
        params: Normalization parameters from normalize_data()
    
    Returns:
        Data in original scale
    """
    if params['method'] == 'minmax':
        return data * (params['max'] - params['min']) + params['min']
    else:  # standard
        return data * params['std'] + params['mean']


class PINNDataset(torch.utils.data.Dataset):
    """
    PyTorch Dataset for PINN training.
    
    Combines:
    - Collocation points (for physics loss)
    - Boundary points (for BC loss)
    - Sensor data (for data loss)
    """
    
    def __init__(self, 
                 collocation_points: Dict[str, torch.Tensor],
                 sensor_data: Optional[Dict[str, torch.Tensor]] = None):
        """
        Args:
            collocation_points: Dict with coordinate tensors
            sensor_data: Dict with 'coords' and 'values' (optional)
        """
        self.collocation_points = collocation_points
        self.sensor_data = sensor_data
        
        # Get number of collocation points
        first_key = list(collocation_points.keys())[0]
        self.n_collocation = len(collocation_points[first_key])
    
    def __len__(self):
        return self.n_collocation
    
    def __getitem__(self, idx):
        # Return collocation point at index
        point = {key: val[idx] for key, val in self.collocation_points.items()}
        return point


# ============================================================
# EXAMPLE USAGE
# ============================================================
if __name__ == "__main__":
    print("Testing data utilities...\n")
    
    # Test 1D collocation points
    print("1. Generating 1D collocation points:")
    points_1d = generate_collocation_points_1d(
        x_range=(0, 1),
        t_range=(0, 1),
        n_points=1000
    )
    print(f"   x shape: {points_1d['x'].shape}")
    print(f"   t shape: {points_1d['t'].shape}")
    print(f"   x range: [{points_1d['x'].min():.3f}, {points_1d['x'].max():.3f}]")
    print(f"   t range: [{points_1d['t'].min():.3f}, {points_1d['t'].max():.3f}]")
    print("   ✅ 1D collocation points working!\n")
    
    # Test 2D collocation points
    print("2. Generating 2D collocation points:")
    points_2d = generate_collocation_points_2d(
        x_range=(0, 10),  # 10 km domain
        y_range=(0, 10),
        t_range=(0, 24),  # 24 hours
        n_points=5000
    )
    print(f"   x shape: {points_2d['x'].shape}")
    print(f"   y shape: {points_2d['y'].shape}")
    print(f"   t shape: {points_2d['t'].shape}")
    print("   ✅ 2D collocation points working!\n")
    
    # Test boundary points
    print("3. Generating boundary points:")
    boundaries = generate_boundary_points_1d(
        x_range=(0, 1),
        t_range=(0, 1),
        n_points=50
    )
    print(f"   Left boundary points: {len(boundaries['left']['x'])}")
    print(f"   Right boundary points: {len(boundaries['right']['x'])}")
    print(f"   Initial condition points: {len(boundaries['initial']['x'])}")
    print("   ✅ Boundary points working!\n")
    
    # Test normalization
    print("4. Testing normalization:")
    data = torch.tensor([10.0, 25.0, 50.0, 35.0, 15.0])  # PM2.5 values
    normalized, params = normalize_data(data, method='minmax')
    recovered = denormalize_data(normalized, params)
    print(f"   Original: {data.numpy()}")
    print(f"   Normalized: {normalized.numpy()}")
    print(f"   Recovered: {recovered.numpy()}")
    print("   ✅ Normalization working!")
