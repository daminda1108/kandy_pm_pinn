"""
Physics Module - Advection-Diffusion Equation for PINN

This module contains functions to compute the physics residuals for the
advection-diffusion equation governing PM2.5 transport:

    ∂C/∂t + u·∇C = D·∇²C + S

Where:
    C = concentration (μg/m³)
    u = (u_x, u_y) wind velocity (m/s)
    D = diffusion coefficient (m²/s)
    S = source term (μg/m³/s)
"""

import torch
import torch.nn as nn


def compute_gradients(output, input_var, create_graph=True):
    """
    Compute gradient of output with respect to input using autograd.
    
    Args:
        output: Tensor - the function output (e.g., concentration C)
        input_var: Tensor - the input variable (e.g., x, y, or t)
        create_graph: bool - whether to create graph for higher-order derivatives
    
    Returns:
        Tensor - gradient dOutput/dInput
    """
    grad = torch.autograd.grad(
        outputs=output,
        inputs=input_var,
        grad_outputs=torch.ones_like(output),
        create_graph=create_graph,
        retain_graph=True
    )[0]
    return grad


def advection_diffusion_residual_1d(model, x, t, u, D, S=0.0):
    """
    Compute 1D advection-diffusion equation residual.
    
    Equation: ∂C/∂t + u·∂C/∂x = D·∂²C/∂x² + S
    
    Args:
        model: Neural network that predicts C given (x, t)
        x: Tensor - spatial coordinate (requires_grad=True)
        t: Tensor - time coordinate (requires_grad=True)
        u: float or Tensor - advection velocity
        D: float or Tensor - diffusion coefficient
        S: float or Tensor - source term (default 0)
    
    Returns:
        Tensor - residual (should be ~0 where physics is satisfied)
    """
    # Ensure gradients are tracked
    x = x.requires_grad_(True)
    t = t.requires_grad_(True)
    
    # Forward pass: predict concentration
    inputs = torch.stack([x, t], dim=-1)
    C = model(inputs)
    
    # First derivatives
    C_t = compute_gradients(C, t)  # ∂C/∂t
    C_x = compute_gradients(C, x)  # ∂C/∂x
    
    # Second derivative
    C_xx = compute_gradients(C_x, x)  # ∂²C/∂x²
    
    # Residual: ∂C/∂t + u·∂C/∂x - D·∂²C/∂x² - S = 0
    residual = C_t + u * C_x - D * C_xx - S
    
    return residual


def advection_diffusion_residual_2d(model, x, y, t, u_x, u_y, D, S=0.0):
    """
    Compute 2D advection-diffusion equation residual.
    
    Equation: ∂C/∂t + u_x·∂C/∂x + u_y·∂C/∂y = D·(∂²C/∂x² + ∂²C/∂y²) + S
    
    Args:
        model: Neural network that predicts C given (x, y, t)
        x: Tensor - x spatial coordinate (requires_grad=True)
        y: Tensor - y spatial coordinate (requires_grad=True)
        t: Tensor - time coordinate (requires_grad=True)
        u_x: float or Tensor - x-component of wind velocity
        u_y: float or Tensor - y-component of wind velocity
        D: float or Tensor - diffusion coefficient
        S: float or Tensor - source term (default 0)
    
    Returns:
        Tensor - residual (should be ~0 where physics is satisfied)
    """
    # Ensure gradients are tracked
    x = x.requires_grad_(True)
    y = y.requires_grad_(True)
    t = t.requires_grad_(True)
    
    # Forward pass: predict concentration
    inputs = torch.stack([x, y, t], dim=-1)
    C = model(inputs)
    
    # First derivatives
    C_t = compute_gradients(C, t)   # ∂C/∂t
    C_x = compute_gradients(C, x)   # ∂C/∂x
    C_y = compute_gradients(C, y)   # ∂C/∂y
    
    # Second derivatives (Laplacian components)
    C_xx = compute_gradients(C_x, x)  # ∂²C/∂x²
    C_yy = compute_gradients(C_y, y)  # ∂²C/∂y²
    
    # Residual: ∂C/∂t + u·∇C - D·∇²C - S = 0
    residual = C_t + u_x * C_x + u_y * C_y - D * (C_xx + C_yy) - S
    
    return residual


class PhysicsLoss(nn.Module):
    """
    Physics loss module for PINN training.
    
    Computes mean squared residual of the advection-diffusion equation
    at collocation points.
    """
    
    def __init__(self, D=1.0, equation_type='1d'):
        """
        Args:
            D: Diffusion coefficient
            equation_type: '1d' or '2d'
        """
        super().__init__()
        self.D = D
        self.equation_type = equation_type
    
    def forward(self, model, collocation_points, velocity, source=0.0):
        """
        Compute physics loss at collocation points.
        
        Args:
            model: Neural network
            collocation_points: dict with 'x', 't' (and 'y' for 2D)
            velocity: float or dict with 'u_x', 'u_y'
            source: Source term value
        
        Returns:
            Tensor - mean squared physics residual
        """
        if self.equation_type == '1d':
            residual = advection_diffusion_residual_1d(
                model=model,
                x=collocation_points['x'],
                t=collocation_points['t'],
                u=velocity,
                D=self.D,
                S=source
            )
        else:  # 2d
            residual = advection_diffusion_residual_2d(
                model=model,
                x=collocation_points['x'],
                y=collocation_points['y'],
                t=collocation_points['t'],
                u_x=velocity['u_x'],
                u_y=velocity['u_y'],
                D=self.D,
                S=source
            )
        
        return torch.mean(residual ** 2)


# ============================================================
# EXAMPLE USAGE (uncomment to test)
# ============================================================
if __name__ == "__main__":
    # Simple test of gradient computation
    print("Testing autograd gradient computation...")
    
    # Create a simple function: f(x) = x^2
    x = torch.tensor([1.0, 2.0, 3.0], requires_grad=True)
    f = x ** 2
    
    # Compute gradient: df/dx = 2x
    df_dx = compute_gradients(f, x)
    
    print(f"x = {x.detach().numpy()}")
    print(f"f(x) = x² = {f.detach().numpy()}")
    print(f"df/dx = 2x = {df_dx.detach().numpy()}")
    print(f"Expected: {2 * x.detach().numpy()}")
    print("✅ Gradient computation working!" if torch.allclose(df_dx, 2*x) else "❌ Error!")
