import numpy as np
import pennylane as qml

def run_1d_cv_vqa_mvp(s0: float, r: float, sigma: float, t: float):
    log_s0 = np.log(s0)
    drift = (r - 0.5 * sigma**2) * t
    vol_scaled = sigma * np.sqrt(t)
    expected_log_st_analytic = log_s0 + drift

    dev = qml.device("default.gaussian", wires=1)

    @qml.qnode(dev)
    def circuit(alpha, r_squeeze):
        qml.Squeezing(r_squeeze, 0, wires=0)
        qml.Displacement(alpha, 0, wires=0)
        return qml.expval(qml.QuadX(0))

    alpha_param = log_s0 + drift
    r_squeeze_param = vol_scaled / 2.0

    raw_exp_x = circuit(alpha_param, r_squeeze_param)
    # PennyLane default.gaussian 下 QuadX 的测量值为 2 * alpha，此处除以 2.0 进行物理标度归一化
    exp_x = raw_exp_x / 2.0

    quantum_estimated_price = np.exp(exp_x + 0.5 * vol_scaled**2)
    analytic_expected_price = np.exp(expected_log_st_analytic + 0.5 * vol_scaled**2)

    return exp_x, expected_log_st_analytic, quantum_estimated_price, analytic_expected_price

if __name__ == "__main__":
    print("=" * 60)
    print("CV-VQA Quantum Option Pricing - Phase 1 MVP Test [VER 3.0 FINAL FIX]")
    print("=" * 60)

    S0 = 100.0
    r = 0.05
    sigma = 0.2
    T = 1.0

    print(f"输入金融参数: S0={S0}, r={r}, sigma={sigma}, T={T}")
    
    q_x, a_x, q_p, a_p = run_1d_cv_vqa_mvp(S0, r, sigma, T)

    print(f"\n[结果对照]")
    print(f"• CV 线路 Log-Price 期望值 <X>: {q_x:.6f}")
    print(f"• 经典解析 Log-Price 期望值:     {a_x:.6f}")
    print(f"• 量子线路预测标的资产期望 E[ST]:   ${q_p:.2f}")
    print(f"• 经典 Black-Scholes 标的资产 E[ST]: ${a_p:.2f}")
    print(f"• 相对误差 (Relative Error):       {abs(q_p - a_p)/a_p * 100:.4f}%")
    print("=" * 60)
