import pennylane as qml
from pennylane import numpy as np
from scipy.stats import norm

# ==========================================
# 1. 金融环境参数定义
# ==========================================
S0 = 100.0
r = 0.05
sigma = 0.2
T = 1.0
K = 100.0

target_drift = (r - 0.5 * sigma**2) * T
target_vol = sigma * np.sqrt(T)
target_log_mean = np.log(S0) + target_drift

# ==========================================
# 2. 基于 Ancilla BeamSplitter 的 CV 硬件损耗线路
# ==========================================
dev = qml.device("default.gaussian", wires=2)

@qml.qnode(dev)
def noisy_circuit(params, loss_rate):
    qml.Squeezing(params[1], 0, wires=0)
    qml.Displacement(params[0], 0, wires=0)
    
    # 通过辅助模 Beam Splitter 模拟硬件光子衰减/损耗
    if loss_rate > 0.0:
        theta = np.arcsin(np.sqrt(loss_rate))
        qml.Beamsplitter(theta, 0.0, wires=[0, 1])
        
    return qml.expval(qml.QuadX(0))

def cost_fn(params, loss_rate):
    q_mean = noisy_circuit(params, loss_rate) / 2.0
    return (q_mean - target_log_mean) ** 2

def run_phase5():
    print("=" * 68)
    print("CV-VQA Quantum Option Pricing - Phase 5: Noise & Robustness Analysis")
    print("=" * 68)

    loss_rates = [0.0, 0.05, 0.10, 0.20] # 0%, 5%, 10%, 20% 光子损耗率
    
    d1 = (np.log(S0 / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    bs_call_price = S0 * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)

    for lr in loss_rates:
        params = np.array([0.1, 0.1], requires_grad=True)
        opt = qml.GradientDescentOptimizer(stepsize=0.15)

        for epoch in range(1, 41):
            params, loss_val = opt.step_and_cost(lambda p: cost_fn(p, lr), params)

        opt_log_mean = noisy_circuit(params, lr) / 2.0
        
        # 蒙特卡洛计算期权价格
        num_samples = 300000
        np.random.seed(42)
        samples_st = np.exp(np.random.normal(opt_log_mean, target_vol, num_samples))
        discounted_price = float(np.exp(-r * T) * np.mean(np.maximum(samples_st - K, 0.0)))
        rel_err = abs(discounted_price - bs_call_price) / bs_call_price * 100

        print(f"• 硬件光子损耗率 (Loss Rate): {int(lr*100):2d}% | <X>: {opt_log_mean:.6f} | VQA定价: USD {discounted_price:.4f} | 相对误差: {rel_err:.4f}%")

    print("=" * 68)
    print(f"• 经典 Black-Scholes 解析价格: USD {bs_call_price:.4f}")
    print("=" * 68)

if __name__ == "__main__":
    run_phase5()
