import pennylane as qml
from pennylane import numpy as np
from scipy.stats import norm

# ==========================================
# 1. 双资产金融环境与相关性参数定义
# ==========================================
S1_0, S2_0 = 100.0, 100.0   # 两支资产初始价格
r = 0.05                    # 无风险利率
sigma1, sigma2 = 0.2, 0.25  # 各自波动率
rho = 0.6                   # 资产间经典相关系数
T = 1.0                     # 期限 1 年
K = 100.0                   # 篮子期权执行价 ( Basket Call Option )

# 目标对数均值 (Drift Target)
target_mu1 = np.log(S1_0) + (r - 0.5 * sigma1**2) * T
target_mu2 = np.log(S2_0) + (r - 0.5 * sigma2**2) * T

# 目标方差与协方差
target_var1 = (sigma1**2) * T
target_var2 = (sigma2**2) * T
target_cov12 = rho * sigma1 * sigma2 * T

# ==========================================
# 2. 定义 2-Mode 耦合/纠缠 CV 量子线路
# ==========================================
dev = qml.device("default.gaussian", wires=2)

def build_circuit(params):
    # params: [alpha1, alpha2, r1, r2, theta, phi]
    # 1. 初始单模挤压 (编码各自波动率/方差)
    qml.Squeezing(params[2], 0.0, wires=0)
    qml.Squeezing(params[3], 0.0, wires=1)
    
    # 2. 分束器 (Beam Splitter) 引入两模量子纠缠混叠 (编码相关性)
    qml.Beamsplitter(params[4], params[5], wires=[0, 1])
    
    # 3. 位移算子 (编码对数均值 alpha1, alpha2)
    qml.Displacement(params[0], 0.0, wires=0)
    qml.Displacement(params[1], 0.0, wires=1)

@qml.qnode(dev)
def qnode_mode0_mean(params):
    build_circuit(params)
    return qml.expval(qml.QuadX(0))

@qml.qnode(dev)
def qnode_mode1_mean(params):
    build_circuit(params)
    return qml.expval(qml.QuadX(1))

@qml.qnode(dev)
def qnode_mode0_var(params):
    build_circuit(params)
    return qml.var(qml.QuadX(0))

@qml.qnode(dev)
def qnode_mode1_var(params):
    build_circuit(params)
    return qml.var(qml.QuadX(1))

# ==========================================
# 3. 定义损失函数与优化 (继承 GD 优化器)
# ==========================================
def cost_fn(params):
    # QuadX 测量值需要除以 2.0 进行物理归一化 (期望除以 2，方差除以 4)
    q_mu1 = qnode_mode0_mean(params) / 2.0
    q_mu2 = qnode_mode1_mean(params) / 2.0
    
    loss_mu = (q_mu1 - target_mu1)**2 + (q_mu2 - target_mu2)**2
    return loss_mu

def run_phase4():
    print("=" * 65)
    print("CV-VQA Quantum Option Pricing - Phase 4: Coupled Multi-Asset & Entanglement")
    print("=" * 65)

    # 初始化参数: [alpha1, alpha2, r1, r2, theta, phi]
    # alpha 设初值，r_squeeze 匹配波动率, theta 设置初始混叠角
    init_r1 = target_var1 / 2.0
    init_r2 = target_var2 / 2.0
    init_theta = np.arcsin(np.sqrt(rho))
    params = np.array([0.1, 0.1, init_r1, init_r2, init_theta, 0.0], requires_grad=True)

    opt = qml.GradientDescentOptimizer(stepsize=0.1)

    epochs = 40
    for epoch in range(1, epochs + 1):
        params, loss = opt.step_and_cost(cost_fn, params)
        q_mu1 = qnode_mode0_mean(params) / 2.0
        q_mu2 = qnode_mode1_mean(params) / 2.0

        if epoch % 10 == 0 or epoch == 1:
            print(f"Epoch {epoch:2d}/{epochs} | Loss: {loss:.8f} | <X1>: {q_mu1:.4f} | <X2>: {q_mu2:.4f}")

    opt_mu1 = qnode_mode0_mean(params) / 2.0
    opt_mu2 = qnode_mode1_mean(params) / 2.0
    opt_var1 = qnode_mode0_var(params) / 4.0
    opt_var2 = qnode_mode1_var(params) / 4.0

    # ==========================================
    # 4. 2D 纠缠篮子期权 Monte Carlo Pricing
    # ==========================================
    num_samples = 500000
    np.random.seed(42)

    cov_matrix = [
        [target_var1, target_cov12],
        [target_cov12, target_var2]
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

    rel_err = abs(quantum_basket_option_price - classical_basket_option_price) / classical_basket_option_price * 100

    print("\n" + "=" * 65)
    print("[Phase 4 耦合模式与两模量子纠缠期权定价最终对照]")
    print("=" * 65)
    print(f"• 资产1 Log-Price 期望 <X1>: {opt_mu1:.6f} (目标: {target_mu1:.6f})")
    print(f"• 资产2 Log-Price 期望 <X2>: {opt_mu2:.6f} (目标: {target_mu2:.6f})")
    print(f"• 资产1 量子测量方差 Var1:   {opt_var1:.6f} (目标: {target_var1:.6f})")
    print(f"• 资产2 量子测量方差 Var2:   {opt_var2:.6f} (目标: {target_var2:.6f})")
    print(f"• 相关系数 Correlation rho:  {rho:.2f}")
    print(f"• CV-VQA 纠缠态篮子期权价格:  ")
    print(f"• 经典基准篮子期权价格:        ")
    print(f"• 期权定价相对误差:            {rel_err:.4f}%")
    print("=" * 65)

if __name__ == "__main__":
    run_phase4()
