import streamlit as st
import plotly.graph_objects as go
from src.engine import QuantumPricingEngine
from src.greeks import GreeksEngine


st.set_page_config(
    page_title="CV-VQA Quantum Pricing Engine Pro", 
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

st.markdown('<p class="main-title">⚛️ CV-VQA Continuous-Variable Quantum Pricing Pro</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">🚀 Advanced Continuous-Variable Quantum Variational Algorithms, Hybrid Simulation & Noise Robustness Analysis</p>', unsafe_allow_html=True)
st.markdown("---")


st.sidebar.markdown("### 🎛️ Control Panel")
st.sidebar.markdown("---")


analysis_mode = st.sidebar.selectbox(
    "Select Simulation Module",
    [
        "📊 Phase 2: VQA Pricing & Convergence", 
        "🛡️ Phase 5: Hardware Photon Loss Robustness"
    ]
)

st.sidebar.header("📊 Market & Hardware Parameters")


S0 = st.sidebar.number_input("Asset Base Price (S0)", min_value=1.0, max_value=500.0, value=100.0, step=1.0)
K = st.sidebar.number_input("Strike Price (K)", min_value=1.0, max_value=500.0, value=100.0, step=1.0)
sigma = st.sidebar.number_input("Volatility (σ)", min_value=0.01, max_value=2.00, value=0.20, step=0.01, format="%.2f")
r = st.sidebar.number_input("Risk-free Rate (r)", min_value=0.0, max_value=0.50, value=0.05, step=0.005, format="%.3f")
T = st.sidebar.number_input("Time to Maturity (T/Years)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)


config = {
    'market': {'S0': S0, 'K': K, 'r': r, 'sigma': sigma, 'T': T},
    'quantum': {'num_wires': 2, 'learning_rate': 0.15, 'max_epochs': 40},
    'simulation': {'monte_carlo_samples': 100000, 'seed': 42}
}

engine = QuantumPricingEngine(config)

if analysis_mode == "📊 Phase 2: VQA Pricing & Convergence":
    loss_rate = st.sidebar.number_input("Hardware Photon Loss Rate", min_value=0.0, max_value=1.0, value=0.0, step=0.01, format="%.2f")
    
    if st.button("🚀 Run Quantum Pricing & Convergence Analysis", type="primary"):
        with st.spinner("🔄 Running quantum circuits and optimizing variational parameters..."):
            res = engine.train_and_price(loss_rate=loss_rate)
            greeks = GreeksEngine.analytical_greeks(S0, K, r, sigma, T)

        st.markdown("### 📈 Simulation Results & Analytics")
        
        
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            st.metric("⚛️ VQA Price", f"USD {res['vqa_price']:.4f}")
        with row1_col2:
            st.metric("📉 BS Price", f"USD {res['bs_price']:.4f}")

        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            st.metric("🎯 Relative Error", f"{res['relative_error_pct']:.4f}%")
        with row2_col2:
            st.metric("📊 Delta (Δ)", f"{greeks['Delta']:.4f}")

        st.markdown("---")
        st.markdown("### 📉 Quantum Optimization Convergence Curve")
        
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=res['loss_history'], 
            mode='lines+markers', 
            name='Loss Value',
            line=dict(color='#6C63FF', width=3),
            marker=dict(size=6)
        ))
        fig.update_layout(
            title="Variational Optimization Loss vs. Epochs",
            xaxis_title="Epoch",
            yaxis_title="Loss Function Value",
            template="plotly_white",
            height=380
        )
        st.plotly_chart(fig, use_container_width=True)
        st.success("✨ Simulation & optimization finished successfully!")

else:
    if st.button("🚀 Run Hardware Noise & Robustness Sweep", type="primary"):
        with st.spinner("🔄 Simulating photon loss across multiple noise rates (0%, 5%, 10%, 20%)..."):
            loss_rates_list = [0.0, 0.05, 0.10, 0.15, 0.20]
            sweep_results = engine.run_noise_sweep(loss_rates_list)

        st.markdown("### 🛡️ Hardware Photon Loss Robustness Report")
        
        rates = [item["loss_rate_pct"] for item in sweep_results]
        prices = [item["vqa_price"] for item in sweep_results]
        errors = [item["relative_error_pct"] for item in sweep_results]

        col_l, col_r = st.columns(2)

        with col_l:
            fig_price = go.Figure()
            fig_price.add_trace(go.Scatter(
                x=rates, y=prices, mode='lines+markers', name='CV-VQA Price',
                line=dict(color='#FF4B4B', width=3), marker=dict(size=8)
            ))
            fig_price.update_layout(
                title="Option Price vs. Photon Loss Rate (%)",
                xaxis_title="Photon Loss Rate (%)",
                yaxis_title="Option Price (USD)",
                template="plotly_white",
                height=350
            )
            st.plotly_chart(fig_price, use_container_width=True)

        with col_r:
            fig_err = go.Figure()
            fig_err.add_trace(go.Bar(
                x=[str(r) + "%" for r in rates], y=errors,
                marker_color='#2ca02c', opacity=0.85
            ))
            fig_err.update_layout(
                title="Relative Error (%) vs. Loss Rate",
                xaxis_title="Hardware Loss Rate",
                yaxis_title="Relative Error (%)",
                template="plotly_white",
                height=350
            )
            st.plotly_chart(fig_err, use_container_width=True)

        st.success("✨ Hardware noise robustness analysis successfully completed!")

