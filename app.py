import streamlit as st
from src.engine import QuantumPricingEngine
from src.greeks import GreeksEngine


st.set_page_config(
    page_title="CV-VQA Quantum Pricing Engine", 
    page_icon="⚛️", 
    layout="wide"
)


st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #FF4B4B, #FF8F00, #6C63FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .sub-title {
        color: #666;
        font-size: 1.1rem;
        margin-top: 5px;
        margin-bottom: 25px;
    }
    </style>
""", unsafe_allow_html=True)


st.markdown('<p class="main-title">⚛️ CV-VQA Continuous-Variable Quantum Pricing</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">🚀 Powered by Continuous-Variable Quantum Variational Algorithms & Hybrid Classical-Quantum Simulation</p>', unsafe_allow_html=True)
st.markdown("---")


st.sidebar.markdown("### 🎛️ Control Panel")
st.sidebar.markdown("---")
st.sidebar.header("📊 Market & Hardware Parameters")


S0 = st.sidebar.number_input("Asset Base Price (S0)", min_value=1.0, max_value=500.0, value=100.0, step=1.0)
sigma = st.sidebar.number_input("Volatility (σ)", min_value=0.01, max_value=2.00, value=0.20, step=0.01, format="%.2f")
r = st.sidebar.number_input("Risk-free Rate (r)", min_value=0.0, max_value=0.50, value=0.05, step=0.005, format="%.3f")
loss_rate = st.sidebar.slider("Hardware Photon Loss Rate", 0.0, 0.30, 0.05, step=0.05)

config = {
    'market': {'S0': S0, 'r': r, 'sigma': sigma, 'T': 1.0, 'K': 100.0},
    'quantum': {'num_wires': 2, 'learning_rate': 0.15, 'max_epochs': 40},
    'simulation': {'monte_carlo_samples': 100000, 'seed': 42}
}


if st.button("🚀 Run Quantum Pricing Simulation", type="primary"):
    with st.spinner("🔄 Running quantum circuits and optimizing parameters... Please wait."):
        engine = QuantumPricingEngine(config)
        res = engine.train_and_price(loss_rate=loss_rate)
        greeks = GreeksEngine.analytical_greeks(S0, 100.0, r, sigma, 1.0)

    st.markdown("### 📈 Simulation Results & Analytics")
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("⚛️ VQA Price", f"USD {res['vqa_price']:.4f}")
    col2.metric("📉 BS Price", f"USD {res['bs_price']:.4f}")
    col3.metric("🎯 Relative Error", f"{res['relative_error_pct']:.4f}%")
    col4.metric("📊 Delta (Δ)", f"{greeks['Delta']:.4f}")

    st.success("✨ Simulation finished successfully! Quantum state optimized.")


