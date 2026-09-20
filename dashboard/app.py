import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os

# Ensure parent path is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from simulation.simulator import Simulator
from slicing.slice_manager import SliceManager
from analysis.evaluator import PerformanceEvaluator
from visualization.plots import PlotGenerator

st.set_page_config(
    page_title="5G Network Slicing Performance Evaluator",
    page_icon="📶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Theme High-Contrast Custom CSS
st.markdown("""
    <style>
    /* Global Page Styling */
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Headers */
    .main-header {
        font-size: 2.2rem;
        color: #38BDF8;
        font-weight: 800;
        margin-bottom: 0.2rem;
        letter-spacing: -0.025em;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #94A3B8;
        margin-bottom: 1.5rem;
        font-weight: 400;
    }

    /* Metric Cards */
    [data-testid="stMetric"] {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        padding: 14px !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important;
    }
    [data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-size: 0.875rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] {
        color: #F8FAFC !important;
        font-size: 1.5rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricDelta"] {
        color: #38BDF8 !important;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #1E293B !important;
        border-right: 1px solid #334155 !important;
    }
    [data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }

    /* Buttons */
    .stButton>button {
        background-color: #0284C7 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 20px !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton>button:hover {
        background-color: #0369A1 !important;
        color: #FFFFFF !important;
        box-shadow: 0 0 12px rgba(56, 189, 248, 0.5) !important;
    }

    /* Download Button */
    .stDownloadButton>button {
        background-color: #10B981 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        border: none !important;
    }
    .stDownloadButton>button:hover {
        background-color: #059669 !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #0F172A;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1E293B !important;
        border-radius: 8px 8px 0 0 !important;
        color: #94A3B8 !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        border: 1px solid #334155 !important;
        border-bottom: none !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0284C7 !important;
        color: #FFFFFF !important;
        border-color: #38BDF8 !important;
    }

    /* DataFrame & Table Dark Mode */
    [data-testid="stDataFrame"] {
        background-color: #1E293B !important;
        border-radius: 8px !important;
    }
    
    /* Dividers */
    hr {
        border-color: #334155 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📶 Performance Evaluation of Network Slicing for 5G Services</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Interactive Simulation & SLA Benchmark Suite for eMBB, URLLC, and mMTC Slices</div>', unsafe_allow_html=True)

st.sidebar.header("⚙️ Simulation Controls")

strategy = st.sidebar.selectbox(
    "Resource Allocation Strategy",
    options=["dynamic", "static"],
    index=0,
    help="Dynamic: Priority & demand-based dynamic sharing. Static: Fixed ratio allocation."
)

traffic_condition = st.sidebar.selectbox(
    "Traffic Condition",
    options=["low", "medium", "high", "congested"],
    index=1
)

total_bandwidth = st.sidebar.slider(
    "Total Substrate Bandwidth (Mbps)",
    min_value=30.0,
    max_value=300.0,
    value=100.0,
    step=10.0
)

total_cpu = st.sidebar.slider(
    "Total CPU Processing Capacity",
    min_value=30.0,
    max_value=300.0,
    value=100.0,
    step=10.0
)

st.sidebar.subheader("User / Device Load Controls")
embb_users = st.sidebar.number_input("eMBB Users", min_value=1, max_value=500, value=50)
urllc_users = st.sidebar.number_input("URLLC Users", min_value=1, max_value=500, value=30)
mmtc_users = st.sidebar.number_input("mMTC Devices", min_value=10, max_value=5000, value=500)

sim_duration = st.sidebar.slider("Simulation Duration (s)", min_value=10, max_value=300, value=60)
random_seed = st.sidebar.number_input("Random Seed", min_value=1, max_value=9999, value=42)

run_button = st.sidebar.button("🚀 Run Simulation", use_container_width=True)

# Instantiates Engine
simulator = Simulator(total_bandwidth_mbps=total_bandwidth, total_cpu=total_cpu, seed=random_seed)
slice_manager = SliceManager(strategy=strategy)
evaluator = PerformanceEvaluator()

user_counts = {
    config.SLICE_EMBB: embb_users,
    config.SLICE_URLLC: urllc_users,
    config.SLICE_MMTC: mmtc_users
}

step_results = simulator.run_step(
    slice_manager=slice_manager,
    traffic_load=traffic_condition,
    user_counts=user_counts,
    duration=float(sim_duration)
)

df_res = evaluator.evaluate_step(
    step_metrics=step_results,
    experiment_id="Interactive_Dashboard_Run",
    traffic_condition=traffic_condition,
    allocation_strategy=strategy,
    users_count=int(sum(user_counts.values()) / 3),
    total_bandwidth=total_bandwidth
)

# Helper function to render dark-themed seaborn plots without deprecation warnings
def render_dark_plot(df: pd.DataFrame, y_col: str, title: str, ylabel: str, palette_name: str):
    fig, ax = plt.subplots(figsize=(6, 4))
    fig.patch.set_facecolor('#1E293B')
    ax.set_facecolor('#1E293B')
    
    sns.barplot(data=df, x="slice_type", y=y_col, hue="slice_type", palette=palette_name, ax=ax, edgecolor="#334155", legend=False)
    
    ax.set_title(title, fontweight="bold", color="#F8FAFC", fontsize=11, pad=10)
    ax.set_xlabel("5G Slice", color="#94A3B8", fontsize=10)
    ax.set_ylabel(ylabel, color="#94A3B8", fontsize=10)
    ax.tick_params(colors="#CBD5E1", labelsize=9)
    ax.grid(True, linestyle="--", alpha=0.2, color="#64748B")
    
    for spine in ax.spines.values():
        spine.set_color('#334155')
        
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

# Tabs Layout
tab1, tab2, tab3, tab4 = st.tabs(["📊 Performance KPIs", "📈 Comparative Charts", "📜 SLA Satisfaction", "📋 Data Table & Exports"])

with tab1:
    st.subheader("Key Performance Indicators (KPIs) by Slice")
    cols = st.columns(3)
    
    for idx, row in df_res.iterrows():
        with cols[idx]:
            st.markdown(f"### {row['slice_type']} Slice")
            st.metric("Overall Score", f"{row['performance_score']:.2f} / 100")
            st.metric("Throughput", f"{row['throughput']:.2f} Mbps", f"Demanded: {row['demand_mbps']:.2f} Mbps")
            st.metric("End-to-End Latency", f"{row['latency']:.2f} ms")
            st.metric("Packet Loss", f"{row['packet_loss']:.2f} %")
            st.metric("Reliability", f"{row['reliability']:.2f} %")
            st.metric("Resource Utilization", f"{row['resource_utilization']:.2f} %")

with tab2:
    st.subheader("Comparative Slicing Visualizations")
    col_a, col_b = st.columns(2)
    
    with col_a:
        render_dark_plot(df_res, "throughput", "Throughput comparison (Mbps)", "Throughput (Mbps)", "Blues_d")
        render_dark_plot(df_res, "packet_loss", "Packet Loss (%)", "Packet Loss (%)", "Reds_d")

    with col_b:
        render_dark_plot(df_res, "latency", "End-to-End Latency (ms)", "Latency (ms)", "Oranges_d")
        render_dark_plot(df_res, "performance_score", "Normalized Performance Score", "Score (0 - 100)", "Greens_d")

with tab3:
    st.subheader("Service Level Agreement (SLA) Compliance Matrix")
    for idx, row in df_res.iterrows():
        slice_type = row["slice_type"]
        sla_met = row["sla_satisfied"]
        pct = row["sla_satisfaction"]
        
        status_icon = "✅ SLA SATISFIED" if sla_met else "❌ SLA BREACHED"
        color = "#22C55E" if sla_met else "#EF4444"
        
        st.markdown(f"#### {slice_type}: <span style='color:{color}; font-weight:700'>{status_icon} ({pct:.1f}%)</span>", unsafe_allow_html=True)
        
        reqs = config.SLA_REQUIREMENTS[slice_type]
        col_req1, col_req2, col_req3 = st.columns(3)
        col_req1.markdown(f"<span style='color:#CBD5E1'>**Target Min Throughput:** {reqs['min_throughput_mbps']} Mbps</span>", unsafe_allow_html=True)
        col_req2.markdown(f"<span style='color:#CBD5E1'>**Target Max Latency:** {reqs['max_latency_ms']} ms</span>", unsafe_allow_html=True)
        col_req3.markdown(f"<span style='color:#CBD5E1'>**Target Max Loss:** {reqs['max_packet_loss_pct']}%</span>", unsafe_allow_html=True)
        st.divider()

with tab4:
    st.subheader("Raw Metrics Data Table")
    st.dataframe(df_res, use_container_width=True)
    
    csv = df_res.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Current Run CSV",
        data=csv,
        file_name="streamlit_slice_simulation_results.csv",
        mime="text/csv"
    )
