import pennylane as qml
from pennylane import numpy as np

# 1. 金融环境参数定义
S0 = 100.0      # 初始标的资产价格
r = 0.05        # 无风险利率
sigma = 0.2     # 波动率
T = 1.0         # 期限 (1年)
K = 100.0       # 敲定价格 (Strike Price)

target_drift = (r - 0.5 * sigma**2) * T
target_vol = sigma * np.sqrt(T)
target_log_mean = np.log(S0) + target_drift

# 2. 定义 PennyLane 设备与变分量子线路
dev = qml.device("default.gaussian", wires=1)

@qml.qnode(dev)
def quantum_circuit(params):
    qml.Squeezing(params[1], 0, wires=0)
    qml.Displacement(params[0], 0, wires=0)
    return qml.expval(qml.QuadX(0))

def cost_fn(params):
    # raw_mean = 2 * alpha
    # q_mean = raw_mean / 2 = alpha
    q_mean = quantum_circuit(params) / 2.0
    return (q_mean - target_log_mean) ** 2

def run_phase2_optimization():
    print("=" * 65)
    print("CV-VQA Quantum Option Pricing - Phase 2: Standard GD Convergence")
    print("=" * 65)

    params = np.array([0.1, 0.1], requires_grad=True)

    # 改用简单的 Standard Gradient Descent 优化器，避开 Adam 动量干扰
    opt = qml.GradientDescentOptimizer(stepsize=0.2)

    epochs = 60
    for epoch in range(1, epochs + 1):
        params, loss = opt.step_and_cost(cost_fn, params)
        q_mean = quantum_circuit(params) / 2.0

        if epoch % 10 == 0 or epoch == 1:
            print(f"Epoch {epoch:2d}/{epochs} | Loss: {loss:.10f} | alpha: {params[0]:.6f} | <X>: {q_mean:.6f}")

    # 3. 训练完成，进行期权 Payoff 定价估算
    opt_log_mean = (quantum_circuit(params) / 2.0)
    
    num_samples = 500000
    np.random.seed(42)
    samples_log_st = np.random.normal(opt_log_mean, target_vol, num_samples)
    samples_st = np.exp(samples_log_st)
    
    payoffs = np.maximum(samples_st - K, 0.0)
    discounted_call_price_vqa = np.exp(-r * T) * np.mean(payoffs)

    # 经典 Black-Scholes 解析解
    from scipy.stats import norm
    d1 = (np.log(S0 / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    bs_call_price = S0 * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)

    print("\n" + "=" * 65)
    print("[Phase 2 变分期权定价最终对照]")
    print("=" * 65)
    print(f"• 变分优化后 Log-Price 期望 <X>: {opt_log_mean:.6f} (目标: {target_log_mean:.6f})")
    print(f"• Quantum VQA 估算看涨期权价格: ${discounted_call_price_vqa:.4f}")
    print(f"• Black-Scholes 解析看涨期权价格: ${bs_call_price:.4f}")
    
    rel_err = abs(discounted_call_price_vqa - bs_call_price) / bs_call_price * 100
    print(f"• 期权定价相对误差:             {rel_err:.4f}%")
    print("=" * 65)

if __name__ == "__main__":
    run_phase2_optimization()
