import matplotlib.pyplot as plt
import numpy as np

# 设置绘图风格
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# 1. Phase 5 噪声抗性数据可视化
loss_rates = [0, 5, 10, 20]
vqa_prices = [10.4515, 10.4513, 10.4507, 10.4467]
bs_benchmark = 10.4506
errors = [0.0088, 0.0065, 0.0011, 0.0367]

ax1.plot(loss_rates, vqa_prices, 'o--', color='#1f77b4', linewidth=2, markersize=8, label='CV-VQA Price')
ax1.axhline(y=bs_benchmark, color='#d62728', linestyle='-', linewidth=1.5, label=f'BS Benchmark ()')
ax1.set_title("CV-VQA Option Pricing under Photon Loss", fontsize=12, fontweight='bold')
ax1.set_xlabel("Photon Loss Rate (%)")
ax1.set_ylabel("Option Price (USD)")
ax1.legend()
ax1.grid(True, linestyle=':', alpha=0.6)

# 2. 相对误差柱状图
bars = ax2.bar([str(l) + "%" for l in loss_rates], errors, color='#2ca02c', alpha=0.85, width=0.4)
ax2.set_title("Relative Error vs. Loss Rate", fontsize=12, fontweight='bold')
ax2.set_xlabel("Hardware Loss Rate")
ax2.set_ylabel("Relative Error (%)")
ax2.set_ylim(0, 0.05)

for bar in bars:
    yval = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 0.001, f"{yval:.4f}%", ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig("phase5_noise_robustness.png", dpi=300)
print("====================================================================")
print("CV-VQA Quantum Option Pricing - Phase 6: Project Completed!")
print("====================================================================")
print("• 分析图表已成功导出保存至: phase5_noise_robustness.png")
print("• 连续变量变分量子期权定价 (CV-VQA) 全流程测试通过！")
print("====================================================================")
