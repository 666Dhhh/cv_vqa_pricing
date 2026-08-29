import pennylane as qml
from pennylane import numpy as np

# ==========================================
# 1. 双资产金融环境与相关性参数定义
# ==========================================
S1_0, S2_0 = 100.0, 100.0   # 两支资产初始价格
r = 0.05                    # 无风险利率
sigma1, sigma2 = 0.2, 0.25  # 各自波动率
rho = 0.6                   # 资产间相关系数
T = 1.0                     # 期限 1 年
K = 100.0                   # 篮子期权执行价 ( Basket Call Option: Mean(S1, S2) )

# 目标对数均值
target_mu1 = np.log(S1_0) + (r - 0.5 * sigma1**2) * T
target_mu2 = np.log(S2_0) + (r - 0.5 * sigma2**2) * T

# ==========================================
# 2. 定义解耦架构的双模式 (2-Mode) CV 量子线路
# ==========================================
dev = qml.device("default.gaussian", wires=2)

def build_circuit(params):
    # 先通过 Beamsplitter 建立纠缠/相关性
    qml.Beamsplitter(params[2], params[3], wires=[0, 1])
    # 再施加独立 Displacement，保证期望值 alpha1, alpha2 完全不受混叠干扰
    qml.Displacement(params[0], 0, wires=0)
    qml.Displacement(params[1], 0, wires=1)

@qml.qnode(dev)
def qnode_mode0(params):
    build_circuit(params)
    return qml.expval(qml.QuadX(0))

@qml.qnode(dev)
def qnode_mode1(params):
    build_circuit(params)
    return qml.expval(qml.QuadX(1))

def cost_fn(params):
    raw_x1 = qnode_mode0(params)
    raw_x2 = qnode_mode1(params)
    q_mu1 = raw_x1 / 2.0
    q_mu2 = raw_x2 / 2.0
    
    # 均值匹配损失
    loss = (q_mu1 - target_mu1)**2 + (q_mu2 - target_mu2)**2
    return loss

def run_phase3_multi_asset():
    print("=" * 65)
    print("CV-VQA Quantum Option Pricing - Phase 3: Decoupled Multi-Asset")
    print("=" * 65)

    # theta 初始化为 arcsin(sqrt(rho)) 以贴合相关性，alpha 设定较小的学习率
    params = np.array([0.1, 0.1, np.arcsin(np.sqrt(rho)), 0.0], requires_grad=True)
    
    # 采用温和的学习率，避免震荡
    opt = qml.GradientDescentOptimizer(stepsize=0.1)

    epochs = 40
    for epoch in range(1, epochs + 1):
        params, loss = opt.step_and_cost(cost_fn, params)
        raw_x1 = qnode_mode0(params)
        raw_x2 = qnode_mode1(params)
        q_mu1, q_mu2 = raw_x1 / 2.0, raw_x2 / 2.0

        if epoch % 10 == 0 or epoch == 1:
            print(f"Epoch {epoch:2d}/{epochs} | Loss: {loss:.8f} | <X1>: {q_mu1:.4f} | <X2>: {q_mu2:.4f}")

    opt_mu1 = qnode_mode0(params) / 2.0
    opt_mu2 = qnode_mode1(params) / 2.0

    # ==========================================
    # 3. 蒙特卡洛采样式 2D 篮子期权 Pricing
    # ==========================================
    num_samples = 500000
    np.random.seed(42)

    cov_matrix = [
        [sigma1**2 * T, rho * sigma1 * sigma2 * T],
        [rho * sigma1 * sigma2 * T, sigma2**2 * T]
    ]
    
    rand_samples = np.random.multivariate_normal([0, 0], cov_matrix, num_samples)
    log_S1 = opt_mu1 + rand_samples[:, 0]
    log_S2 = opt_mu2 + rand_samples[:, 1]

    S1_T = np.exp(log_S1)
    S2_T = np.exp(log_S2)

    basket_price = 0.5 * (S1_T + S2_T)
    payoffs = np.maximum(basket_price - K, 0.0)
    quantum_basket_option_price = np.exp(-r * T) * np.mean(payoffs)

    # 经典对照组
    rand_samples_ref = np.random.multivariate_normal([0, 0], cov_matrix, num_samples)
    ref_S1 = np.exp(target_mu1 + rand_samples_ref[:, 0])
    ref_S2 = np.exp(target_mu2 + rand_samples_ref[:, 1])
    ref_payoffs = np.maximum(0.5 * (ref_S1 + ref_S2) - K, 0.0)
    classical_basket_option_price = np.exp(-r * T) * np.mean(ref_payoffs)

    print("\n" + "=" * 65)
    print("[Phase 3 双资产篮子期权定价最终对照]")
    print("=" * 65)
    print(f"• 资产1 Log-Price 期望 <X1>: {opt_mu1:.6f} (目标: {target_mu1:.6f})")
    print(f"• 资产2 Log-Price 期望 <X2>: {opt_mu2:.6f} (目标: {target_mu2:.6f})")
    print(f"• 相关系数 Correlation rho:  {rho:.2f}")
    print(f"• CV-VQA 篮子期权估算价格:    ${quantum_basket_option_price:.4f}")
    print(f"• 经典基准篮子期权价格:        ${classical_basket_option_price:.4f}")
    
    rel_err = abs(quantum_basket_option_price - classical_basket_option_price) / classical_basket_option_price * 100
    print(f"• 期权定价相对误差:             {rel_err:.4f}%")
    print("=" * 65)

if __name__ == "__main__":
    run_phase3_multi_asset()
