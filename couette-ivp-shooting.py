import time

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import root_scalar
from scipy.io import savemat
import matplotlib.pyplot as plt
from mplcursors import cursor

# Constants
Pr = 0.72  # value for air
gamma = 1.4  # value for air
C = 0.5  # given
# Mach numbers to test
M = np.linspace(0, 10, 51)
# M = [0.5, 1, 2] # Mach numbers used in the paper

T_r = lambda M: 1 + (gamma - 1) / 2 * Pr * M * M

def solve(C, gamma, M_r):
    """Solves ODE system using solve_ivp and root_scalar"""
    
    def ode_system(X, tau, C, gamma, M_r):
        """Define the system of ODEs"""
        U0, T = X
        
        # Viscosity
        etaRecip = (np.maximum(T, 1e-10) + C) / (np.maximum(T, 1e-10) ** (3 / 2) * (1 + C))  # equation 14
        
        # Derivatives
        dU0_dy = tau * etaRecip  # equation 10
        dT_dy = -(Pr * etaRecip) * ((gamma - 1) * M_r * M_r * tau * U0)  # equation 11
        
        return [dU0_dy, dT_dy]
    
    def shoot(tau, C, gamma, M_r):
        """Shooting method"""
        Tr = T_r(M_r)  # Recovery temperature
        y_span = (0, 1)
        X0 = [0, Tr]  # Initial conditions: U0(0) = 0, T(0) = Tr
        
        sol = solve_ivp(lambda y, X: ode_system(X, tau, C, gamma, M_r), y_span, X0, dense_output=True)
        
        return sol.sol(1)[0] - 1  # Return the boundary condition residual

    tau_guess = 1 + M_r / 2

    root_result = root_scalar(lambda tau: shoot(tau, C, gamma, M_r), 
                              method='brentq', 
                              bracket=[0.1, M_r + 1], 
                              x0=tau_guess)
    
    if not root_result.converged:
        raise ValueError(f"Root finding failed to converge: {root_result.flag}")
    
    tau_solution = root_result.root
    print(f"Root found: tau = {tau_solution:.6f}, iterations: {root_result.iterations}")
    
    y_span = (0, 1)
    X0 = [0, T_r(M_r)]
    sol = solve_ivp(lambda y, X: ode_system(X, tau_solution, C, gamma, M_r), y_span, X0, dense_output=True)
    
    y = np.linspace(0, 1, 3001)
    X = sol.sol(y)
    U0, T = X
    T += 1 - T[-1]  # enforce boundary condition of T0(1) = 1
    eta = T ** (3 / 2) * (1 + C) / (T + C)  # calculate viscosity
    
    return y, U0, T, eta, T

# Main calculation and plotting code
plt.figure(figsize=(12, 5)) # 8, 7
styles = ["solid", "dashed", "dotted"]
data = {"y": [], "M_r": [M], "U0": [], "T": [], "eta": [], "xi": []}

for i, M_r in enumerate(M):
    print(f'\nCalculating mach {M_r:.2f}')
    try:
        y, U0, T, eta, xi = solve(C, gamma, M_r)
    except ValueError as e:
        print(f"Error for M_r = {M_r}: {e}")
        continue
    if i == 0:
        data["y"].append(list(y))
    data["U0"].append(list(U0))#*M_r))
    data["T"].append(list(T))
    data["eta"].append(list(eta))
    data["xi"].append(list(xi))
    
    # Velocity
    plt.subplot(1, 2, 1)
    plt.axis((0, 1, 0, 1))
    plt.plot(U0, y, label=f"Mr = {M_r}", linestyle=styles[i % len(styles)])
    plt.ylabel("y")
    plt.xlabel("U0")
    plt.title("Velocity")
    # plt.legend()
    
    # Temperature
    plt.subplot(1, 2, 2)
    plt.axis((1, max(T) * 1.1, 0, 1))
    plt.plot(T, y, label=f"Mr = {M_r}", linestyle=styles[i % 3])
    plt.ylabel("y")
    plt.xlabel("T0")
    plt.title("Temperature")
    
    # # Specific volume (xi)
    # plt.subplot(2, 2, 3)
    # plt.axis((1, max(xi) * 1.1, 0, 1))
    # plt.plot(T, y, label=f"Mr = {M_r}", linestyle=styles[i % 3])
    # plt.ylabel("y")
    # plt.xlabel("Xi0")
    # plt.title("Specific volume")
    
    # # Viscosity coefficient (eta)
    # plt.subplot(2, 2, 4)
    # plt.axis((0.9, max(eta) * 1.1, 0, 1))
    # plt.plot(eta, y, label=f"Mr = {M_r}", linestyle=styles[i % 3])
    # plt.ylabel("y")
    # plt.xlabel("Eta0")
    # plt.title("Viscosity coefficient")

savemat(f"export/ivp_couette_data_{hex(round(time.time()))[2:]}.mat", data)

cursor(hover=True)
plt.tight_layout()
plt.show()

# Additional plots
y = data['y'][0]
U0 = data['U0']
T = data['T']
M_r = data['M_r'][0]

plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.imshow(
    np.rot90(U0),
    aspect="auto",
    origin="upper",
    extent=[min(M_r), max(M_r), 0, 1],
    cmap="plasma",
)
plt.colorbar(label="U")
plt.title("Velocity")
plt.xlabel("M_r")
plt.ylabel("y")

plt.subplot(1, 2, 2)
plt.imshow(
    np.rot90(T),
    aspect="auto",
    origin="upper",
    extent=[min(M_r), max(M_r), 0, 1],
    cmap="plasma",
)
plt.colorbar(label="T")
plt.title("Temperature")
plt.xlabel("M_r")
plt.ylabel("y")

plt.tight_layout()
plt.show()