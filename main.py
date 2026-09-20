import argparse
import sys
import os
import pandas as pd
import config
from simulation.simulator import Simulator
from slicing.slice_manager import SliceManager
from analysis.evaluator import PerformanceEvaluator
from visualization.plots import PlotGenerator
from experiments.run_experiments import ExperimentRunner

def main():
    parser = argparse.ArgumentParser(
        description="5G Network Slicing Performance Evaluation System CLI"
    )
    
    parser.add_argument("--duration", type=float, default=60.0, help="Simulation duration in seconds (default: 60.0)")
    parser.add_argument("--traffic", type=str, default="medium", choices=["low", "medium", "high", "congested"], help="Traffic condition level (default: medium)")
    parser.add_argument("--strategy", type=str, default="dynamic", choices=["dynamic", "static"], help="Resource allocation strategy (default: dynamic)")
    parser.add_argument("--users", type=int, default=100, help="Average number of users per slice (default: 100)")
    parser.add_argument("--bandwidth", type=float, default=config.DEFAULT_TOTAL_BANDWIDTH, help="Total physical substrate bandwidth in Mbps (default: 100.0)")
    parser.add_argument("--cpu", type=float, default=None, help="Total physical substrate CPU capacity (default: matches bandwidth)")
    parser.add_argument("--seed", type=int, default=config.DEFAULT_RANDOM_SEED, help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--run-experiments", action="store_true", help="Execute the complete suite of 8 automated experiments")

    args = parser.parse_args()
    if args.cpu is None:
        args.cpu = args.bandwidth

    if args.run_experiments:
        print("Running full automated experiment suite (Experiments 1 - 8)...")
        runner = ExperimentRunner(seed=args.seed)
        runner.run_all_experiments()
        return

    print("==========================================================================")
    print("       5G Network Slicing Performance Evaluation System Simulation        ")
    print("==========================================================================")
    print(f" Strategy: {args.strategy.upper()} Allocation")
    print(f" Traffic Condition: {args.traffic.upper()}")
    print(f" Substrate Bandwidth: {args.bandwidth} Mbps | CPU Capacity: {args.cpu} units")
    print(f" Simulation Duration: {args.duration}s | Random Seed: {args.seed}")
    print("--------------------------------------------------------------------------")

    # Scale default slice user counts according to --users argument ratio
    scale = args.users / 100.0
    user_counts = {
        config.SLICE_EMBB: max(1, int(50 * scale)),
        config.SLICE_URLLC: max(1, int(30 * scale)),
        config.SLICE_MMTC: max(1, int(500 * scale))
    }

    # Run Simulation Engine
    simulator = Simulator(total_bandwidth_mbps=args.bandwidth, total_cpu=args.cpu, seed=args.seed)
    slice_manager = SliceManager(strategy=args.strategy)
    evaluator = PerformanceEvaluator()
    plotter = PlotGenerator()

    step_results = simulator.run_step(
        slice_manager=slice_manager,
        traffic_load=args.traffic,
        user_counts=user_counts,
        duration=args.duration
    )

    df_res = evaluator.evaluate_step(
        step_metrics=step_results,
        experiment_id="CLI_Single_Run",
        traffic_condition=args.traffic,
        allocation_strategy=args.strategy,
        users_count=args.users,
        total_bandwidth=args.bandwidth
    )

    csv_path, json_path = evaluator.export_results(df_res, filename_stem="cli_simulation_run")
    plot_files = plotter.generate_all_single_run_plots(df_res)

    print("\nSimulation Metrics & Evaluation Results:")
    print("--------------------------------------------------------------------------")
    display_cols = ["slice_type", "demand_mbps", "allocated_bw_mbps", "throughput", "latency", "packet_loss", "reliability", "sla_satisfied", "performance_score"]
    print(df_res[display_cols].to_string(index=False))
    print("--------------------------------------------------------------------------")
    print(f" Results exported to: {csv_path}")
    print(f" Plots generated in: {config.PLOTS_DIR}")
    print("==========================================================================\n")

if __name__ == "__main__":
    main()
