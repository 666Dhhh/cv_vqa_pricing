import pennylane as qml
from pennylane import numpy as np

class CVOptionCircuit:
    """连续变量变分量子期权定价线路类 (Continuous-Variable VQA Circuit)"""
    
    def __init__(self, num_wires: int = 2, device_name: str = "default.gaussian"):
        self.num_wires = num_wires
        self.dev = qml.device(device_name, wires=num_wires)
        self._qnode = qml.QNode(self._circuit_definition, self.dev)

    def _circuit_definition(self, params: np.ndarray, loss_rate: float):
        qml.Squeezing(params[1], 0, wires=0)
        qml.Displacement(params[0], 0, wires=0)
        
        if loss_rate > 0.0:
            theta = np.arcsin(np.sqrt(loss_rate))
            qml.Beamsplitter(theta, 0.0, wires=[0, 1])
            
        return qml.expval(qml.QuadX(0))

    def evaluate(self, params: np.ndarray, loss_rate: float = 0.0) -> float:
        raw_val = self._qnode(params, loss_rate)
        return float(raw_val) / 2.0
