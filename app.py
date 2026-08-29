import streamlit as st
from src.engine import QuantumPricingEngine
from src.greeks import GreeksEngine

st.set_page_config(page_title="CV-VQA Quantum Pricing Engine", layout="wide")

st.title("⚡ CV-VQA Continuous-Variable Quantum Option Pricing Dashboard")
st.markdown("---")

st.sidebar.header("📊 Market & Hardware Parameters")
S0 = st.sidebar.slider("Asset Base Price (S0)", 50.0, 150.0, 100.0)
sigma = st.sidebar.slider("Volatility (sigma)", 0.05, 0.50, 0.20)
r = st.sidebar.slider("Risk-free Rate (r)", 0.01, 0.10, 0.05)
loss_rate = st.sidebar.slider("Hardware Photon Loss Rate", 0.0, 0.30, 0.05, step=0.05)

config = {
    'market': {'S0': S0, 'r': r, 'sigma': sigma, 'T': 1.0, 'K': 100.0},
    'quantum': {'num_wires': 2, 'learning_rate': 0.15, 'max_epochs': 40},
    'simulation': {'monte_carlo_samples': 100000, 'seed': 42}
}

if st.button("🚀 Run Quantum Pricing Simulation"):
    engine = QuantumPricingEngine(config)
    res = engine.train_and_price(loss_rate=loss_rate)
    greeks = GreeksEngine.analytical_greeks(S0, 100.0, r, sigma, 1.0)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("VQA Price", f"USD {res['vqa_price']:.4f}")
    col2.metric("BS Price", f"USD {res['bs_price']:.4f}")
    col3.metric("Relative Error", f"{res['relative_error_pct']:.4f}%")
    col4.metric("Delta (Δ)", f"{greeks['Delta']:.4f}")

    st.success("Simulation finished successfully!")
