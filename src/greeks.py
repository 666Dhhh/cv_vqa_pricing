import numpy as np
from scipy.stats import norm

class GreeksEngine:
    """期权风险指标 (Greeks) 计算模块"""
    
    @staticmethod
    def analytical_greeks(S0: float, K: float, r: float, sigma: float, T: float) -> dict:
        d1 = (np.log(S0 / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        delta = norm.cdf(d1)
        gamma = norm.pdf(d1) / (S0 * sigma * np.sqrt(T))
        vega = S0 * norm.pdf(d1) * np.sqrt(T)
        theta = -(S0 * norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * norm.cdf(d2)
        
        return {"Delta": delta, "Gamma": gamma, "Vega": vega, "Theta": theta}
