import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import List
import config

# Set plot style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
SLICE_COLORS = {
    config.SLICE_EMBB: '#1f77b4',   # Royal Blue
    config.SLICE_URLLC: '#d62728',  # Crimson Red
    config.SLICE_MMTC: '#2ca02c'   # Forest Green
}

class PlotGenerator:
    """
    Generates publication-quality charts for 5G network slicing performance evaluation.
    Saves plots automatically to config.PLOTS_DIR.
    """

    def __init__(self, output_dir: str = config.PLOTS_DIR):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_slice_bar_chart(self, df: pd.DataFrame, metric: str, title: str, ylabel: str, filename: str):
        """Helper to generate standard bar charts grouped by slice."""
        fig, ax = plt.subplots(figsize=(8, 5))
        
        slices = df["slice_type"].unique()
        colors = [SLICE_COLORS.get(s, '#333333') for s in slices]
        
        bars = ax.bar(df["slice_type"], df[metric], color=colors, width=0.5, edgecolor='black', alpha=0.85)
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel("5G Network Slice", fontsize=12, labelpad=10)
        ax.set_ylabel(ylabel, fontsize=12, labelpad=10)
        ax.grid(True, linestyle='--', alpha=0.5)

        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.2f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=10, fontweight='bold')

        plt.tight_layout()
        filepath = os.path.join(self.output_dir, filename)
        plt.savefig(filepath, dpi=300)
        plt.close()
        return filepath

    def generate_all_single_run_plots(self, df: pd.DataFrame) -> List[str]:
        """Generates plots 1 through 8 for a single simulation run."""
        generated_files = []

        # 1. Throughput vs Slice
        generated_files.append(self.generate_slice_bar_chart(
            df, "throughput", "Throughput across 5G Network Slices", "Throughput (Mbps)", "1_throughput_vs_slice.png"
        ))

        # 2. Latency vs Slice
        generated_files.append(self.generate_slice_bar_chart(
            df, "latency", "End-to-End Latency across 5G Network Slices", "Latency (ms)", "2_latency_vs_slice.png"
        ))

        # 3. Packet Loss vs Slice
        generated_files.append(self.generate_slice_bar_chart(
            df, "packet_loss", "Packet Loss Percentage across 5G Slices", "Packet Loss (%)", "3_packet_loss_vs_slice.png"
        ))

        # 4. Jitter vs Slice
        generated_files.append(self.generate_slice_bar_chart(
            df, "jitter", "Jitter across 5G Network Slices", "Jitter (ms)", "4_jitter_vs_slice.png"
        ))

        # 5. Resource Utilization vs Slice
        generated_files.append(self.generate_slice_bar_chart(
            df, "resource_utilization", "Resource Utilization across 5G Slices", "Resource Utilization (%)", "5_resource_utilization_vs_slice.png"
        ))

        # 6. Reliability vs Slice
        generated_files.append(self.generate_slice_bar_chart(
            df, "reliability", "Reliability across 5G Network Slices", "Reliability (%)", "6_reliability_vs_slice.png"
        ))

        # 7. SLA Satisfaction vs Slice
        generated_files.append(self.generate_slice_bar_chart(
            df, "sla_satisfaction", "SLA Satisfaction Percentage across 5G Slices", "SLA Satisfaction (%)", "7_sla_satisfaction_vs_slice.png"
        ))

        # 8. Performance Score vs Slice
        generated_files.append(self.generate_slice_bar_chart(
            df, "performance_score", "Normalized Performance Score across 5G Slices", "Performance Score (0 - 100)", "8_performance_score_vs_slice.png"
        ))

        # 11. Resource Allocation Comparison (Demand vs Allocated)
        fig, ax = plt.subplots(figsize=(9, 5))
        x = range(len(df))
        width = 0.35
        ax.bar([i - width/2 for i in x], df["demand_mbps"], width, label='Demanded Bandwidth (Mbps)', color='#ff7f0e', edgecolor='black')
        ax.bar([i + width/2 for i in x], df["allocated_bw_mbps"], width, label='Allocated Bandwidth (Mbps)', color='#2ca02c', edgecolor='black')
        ax.set_xticks(x)
        ax.set_xticklabels(df["slice_type"])
        ax.set_title("11. Resource Allocation Comparison (Demand vs Allocated)", fontsize=14, fontweight='bold')
        ax.set_ylabel("Bandwidth (Mbps)", fontsize=12)
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        path11 = os.path.join(self.output_dir, "11_resource_allocation_comparison.png")
        plt.savefig(path11, dpi=300)
        plt.close()
        generated_files.append(path11)

        return generated_files

    def plot_throughput_vs_traffic_load(self, exp_df: pd.DataFrame) -> str:
        """9. Throughput vs Traffic Load"""
        fig, ax = plt.subplots(figsize=(9, 5))
        sns.lineplot(data=exp_df, x="traffic_condition", y="throughput", hue="slice_type", marker="o", linewidth=2.5, palette=SLICE_COLORS, ax=ax)
        ax.set_title("9. Throughput vs Traffic Load Level", fontsize=14, fontweight='bold')
        ax.set_xlabel("Traffic Condition", fontsize=12)
        ax.set_ylabel("Throughput (Mbps)", fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        path = os.path.join(self.output_dir, "9_throughput_vs_traffic_load.png")
        plt.savefig(path, dpi=300)
        plt.close()
        return path

    def plot_latency_vs_traffic_load(self, exp_df: pd.DataFrame) -> str:
        """10. Latency vs Traffic Load"""
        fig, ax = plt.subplots(figsize=(9, 5))
        sns.lineplot(data=exp_df, x="traffic_condition", y="latency", hue="slice_type", marker="s", linewidth=2.5, palette=SLICE_COLORS, ax=ax)
        ax.set_title("10. Latency vs Traffic Load Level", fontsize=14, fontweight='bold')
        ax.set_xlabel("Traffic Condition", fontsize=12)
        ax.set_ylabel("End-to-End Latency (ms)", fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        path = os.path.join(self.output_dir, "10_latency_vs_traffic_load.png")
        plt.savefig(path, dpi=300)
        plt.close()
        return path

    def plot_static_vs_dynamic(self, exp_df: pd.DataFrame) -> str:
        """12. Static vs Dynamic Allocation comparison chart"""
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(data=exp_df, x="slice_type", y="performance_score", hue="allocation_strategy", palette="Set2", ax=ax, edgecolor='black')
        ax.set_title("12. Static vs Dynamic Resource Allocation Strategy", fontsize=14, fontweight='bold')
        ax.set_xlabel("5G Network Slice", fontsize=12)
        ax.set_ylabel("Performance Score (0 - 100)", fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        path = os.path.join(self.output_dir, "12_static_vs_dynamic_allocation.png")
        plt.savefig(path, dpi=300)
        plt.close()
        return path

    def plot_performance_vs_users(self, exp_df: pd.DataFrame) -> str:
        """13. Performance vs Number of Users"""
        fig, ax = plt.subplots(figsize=(9, 5))
        sns.lineplot(data=exp_df, x="users", y="performance_score", hue="slice_type", marker="^", linewidth=2.5, palette=SLICE_COLORS, ax=ax)
        ax.set_title("13. Performance Score vs Number of Connected Users/Devices", fontsize=14, fontweight='bold')
        ax.set_xlabel("Number of Connected Users / Devices", fontsize=12)
        ax.set_ylabel("Performance Score (0 - 100)", fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        path = os.path.join(self.output_dir, "13_performance_vs_users.png")
        plt.savefig(path, dpi=300)
        plt.close()
        return path

    def plot_performance_vs_bandwidth(self, exp_df: pd.DataFrame) -> str:
        """14. Performance vs Available Bandwidth"""
        fig, ax = plt.subplots(figsize=(9, 5))
        sns.lineplot(data=exp_df, x="bandwidth", y="performance_score", hue="slice_type", marker="D", linewidth=2.5, palette=SLICE_COLORS, ax=ax)
        ax.set_title("14. Performance Score vs Substrate Bandwidth Capacity", fontsize=14, fontweight='bold')
        ax.set_xlabel("Total Substrate Bandwidth (Mbps)", fontsize=12)
        ax.set_ylabel("Performance Score (0 - 100)", fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        path = os.path.join(self.output_dir, "14_performance_vs_bandwidth.png")
        plt.savefig(path, dpi=300)
        plt.close()
        return path
