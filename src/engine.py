import numpy as np
from scipy.stats import norm
import pennylane as qml
from pennylane import numpy as pnp
from src.circuits import CVOptionCircuit

class QuantumPricingEngine:
    
    
    def __init__(self, config: dict):
        self.cfg = config
        self.circuit_model = CVOptionCircuit(num_wires=config['quantum']['num_wires'])

    def black_scholes_price(self, S0: float, K: float, r: float, sigma: float, T: float) -> float:
        d1 = (np.log(S0 / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        return float(S0 * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2))

    def train_and_price(self, loss_rate: float = 0.0) -> dict:
        S0, r, sigma, T, K = (self.cfg['market'][k] for k in ['S0', 'r', 'sigma', 'T', 'K'])
        target_drift = (r - 0.5 * sigma**2) * T
        target_log_mean = np.log(S0) + target_drift
        target_vol = sigma * np.sqrt(T)

        params = pnp.array([0.1, 0.1], requires_grad=True)
        opt = qml.GradientDescentOptimizer(stepsize=self.cfg['quantum']['learning_rate'])

        def cost_fn(p):
            q_mean = self.circuit_model._qnode(p, loss_rate) / 2.0
            return (q_mean - target_log_mean) ** 2

        
        loss_history = []
        for _ in range(self.cfg['quantum']['max_epochs']):
            params, loss_val = opt.step_and_cost(cost_fn, params)
            loss_history.append(float(loss_val))

        opt_log_mean = self.circuit_model.evaluate(params, loss_rate)
        
        num_samples = self.cfg['simulation']['monte_carlo_samples']
        np.random.seed(self.cfg['simulation']['seed'])
        samples_st = np.exp(np.random.normal(opt_log_mean, target_vol, num_samples))
        vqa_price = float(np.exp(-r * T) * np.mean(np.maximum(samples_st - K, 0.0)))
        
        bs_price = self.black_scholes_price(S0, K, r, sigma, T)
        rel_error = abs(vqa_price - bs_price) / bs_price * 100.0

        return {
            "vqa_price": vqa_price,
            "bs_price": bs_price,
            "relative_error_pct": rel_error,
            "optimized_log_mean": opt_log_mean,
            "loss_history": loss_history  
        }

    def run_noise_sweep(self, loss_rates: list) -> list:
        
        results = []
        for lr in loss_rates:
            res = self.train_and_price(loss_rate=lr)
            results.append({
                "loss_rate_pct": int(lr * 100),
                "vqa_price": res["vqa_price"],
                "relative_error_pct": res["relative_error_pct"]
            })
        return results

