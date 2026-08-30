import pennylane as qml
from pennylane import numpy as np
from scipy.stats import norm

print("=================================================================")
print("CV-VQA Quantum Option Pricing - Phase 4: Coupled Multi-Asset & Entanglement (Standalone)")
print("=================================================================\n")

# 1. 金融衍生品与篮子期权参数设定
S1_0, S2_0 = 100.0, 100.0   # 初始资产价格
K = 100.0                   # 篮子期权执行价
r = 0.05                    # 无风险利率
T = 1.0                     # 期限 (1年)
sigma1, sigma2 = 0.20, 0.25 # 各自波动率
target_rho = 0.60           # 两资产经典相关系数
weights = (0.5, 0.5)        # 篮子权重

target_mu1 = np.log(S1_0) + (r - 0.5 * sigma1**2) * T
target_mu2 = np.log(S2_0) + (r - 0.5 * sigma2**2) * T
target_var1 = (sigma1**2) * T
target_var2 = (sigma2**2) * T
target_cov12 = target_rho * sigma1 * sigma2 * T

# 2. 构建 2-Mode 耦合/纠缠 CV 量子设备与测量线路 (使用标准 QuadX 算子)
dev = qml.device("default.gaussian", wires=2)

def _apply_circuit(params):
    r1, r2, theta, phi, alpha1, alpha2 = params
    qml.Squeezing(r1, 0.0, wires=0)
    qml.Squeezing(r2, 0.0, wires=1)
    qml.Beamsplitter(theta, phi, wires=[0, 1])
    qml.Displacement(alpha1, 0.0, wires=0)
    qml.Displacement(alpha2, 0.0, wires=1)

@qml.qnode(dev)
def circuit_x0(params):
    _apply_circuit(params)
    return qml.expval(qml.QuadX(0))

@qml.qnode(dev)
def circuit_x1(params):
    _apply_circuit(params)
    return qml.expval(qml.QuadX(1))

@qml.qnode(dev)
def circuit_var_x0(params):
    _apply_circuit(params)
    return qml.var(qml.QuadX(0))

@qml.qnode(dev)
def circuit_var_x1(params):
    _apply_circuit(params)
    return qml.var(qml.QuadX(1))

def get_circuit_outputs(params):
    r1, r2, theta, phi, alpha1, alpha2 = params
    exp_x1 = circuit_x0(params) / 2.0
    exp_x2 = circuit_x1(params) / 2.0
    var_x1 = circuit_var_x0(params) / 4.0
    var_x2 = circuit_var_x1(params) / 4.0
    
    cov_x1x2 = 0.5 * (np.exp(2 * r1) - np.exp(2 * r2)) * np.sin(2 * theta) * np.cos(phi) / 4.0
    return exp_x1, exp_x2, var_x1, var_x2, cov_x1x2

def cost_function(params):
    exp_x1, exp_x2, var_x1, var_x2, measured_cov = get_circuit_outputs(params)
    loss_mu1 = (exp_x1 - target_mu1)**2
    loss_mu2 = (exp_x2 - target_mu2)**2
    loss_var1 = (var_x1 - target_var1)**2
    loss_var2 = (var_x2 - target_var2)**2
    loss_cov = (measured_cov - target_cov12)**2
    return loss_mu1 + loss_mu2 + loss_var1 + loss_var2 + 10.0 * loss_cov

# 4. 变分优化循环
params = np.array([0.1, 0.1, 0.2, 0.0, 1.0, 1.0], requires_grad=True)
opt = qml.AdamOptimizer(stepsize=0.08)

epochs = 40
print("正在优化两模纠缠量子电路参数...")
for epoch in range(1, epochs + 1):
    params, loss_val = opt.step_and_cost(cost_function, params)
    if epoch == 1 or epoch % 10 == 0:
        exp_x1, exp_x2, var_x1, var_x2, meas_cov = get_circuit_outputs(params)
        print(f"Epoch {epoch:2d}/{epochs} | Loss: {loss_val:.8f} | <X1>: {exp_x1:.4f} | <X2>: {exp_x2:.4f}")

# 5. 测算与篮子期权定价对比
final_exp_x1, final_exp_x2, final_var_x1, final_var_x2, final_cov = get_circuit_outputs(params)
final_rho = final_cov / np.sqrt(final_var_x1 * final_var_x2 + 1e-12)

w1, w2 = weights
basket_0 = w1 * S1_0 + w2 * S2_0
sigma_basket = np.sqrt(
    (w1 * S1_0 / basket_0)**2 * sigma1**2 +
    (w2 * S2_0 / basket_0)**2 * sigma2**2 +
    2 * (w1 * S1_0 / basket_0) * (w2 * S2_0 / basket_0) * target_rho * sigma1 * sigma2
)

d1 = (np.log(basket_0 / K) + (r + 0.5 * sigma_basket**2) * T) / (sigma_basket * np.sqrt(T))
d2 = d1 - sigma_basket * np.sqrt(T)
benchmark_basket_price = np.exp(-r * T) * (basket_0 * np.exp(r * T) * norm.cdf(d1) - K * norm.cdf(d2))

sigma_basket_vqa = np.sqrt(
    (w1 * S1_0 / basket_0)**2 * final_var_x1 +
    (w2 * S2_0 / basket_0)**2 * final_var_x2 +
    2 * (w1 * S1_0 / basket_0) * (w2 * S2_0 / basket_0) * final_rho * np.sqrt(final_var_x1) * np.sqrt(final_var_x2)
)
d1_vqa = (np.log(basket_0 / K) + (r + 0.5 * sigma_basket_vqa**2) * T) / (sigma_basket_vqa * np.sqrt(T))
d2_vqa = d1_vqa - sigma_basket_vqa * np.sqrt(T)
vqa_basket_price = np.exp(-r * T) * (basket_0 * np.exp(r * T) * norm.cdf(d1_vqa) - K * norm.cdf(d2_vqa))

rel_error_price = abs(vqa_basket_price - benchmark_basket_price) / benchmark_basket_price * 100

print("\n=================================================================")
print("[Phase 4 耦合模式与两模量子纠缠期权定价最终对照]")
print("=================================================================")
print(f"• 资产1 Log-Price 期望 <X1>:  {final_exp_x1:.6f} (目标: {target_mu1:.6f})")
print(f"• 资产2 Log-Price 期望 <X2>:  {final_exp_x2:.6f} (目标: {target_mu2:.6f})")
print(f"• 量子纠缠测得相关系数 rho:  {final_rho:.6f} (目标 rho: {target_rho:.2f})")
print(f"• 测得协方差 Covariance:       {final_cov:.6f} (目标 Cov: {target_cov12:.6f})")
print(f"• CV-VQA 纠缠态篮子期权价格:   ${vqa_basket_price:.4f}")
print(f"• 经典基准篮子期权价格:       ${benchmark_basket_price:.4f}")
print(f"• 期权定价相对误差:            {rel_error_price:.4f}%")
print("=================================================================")


