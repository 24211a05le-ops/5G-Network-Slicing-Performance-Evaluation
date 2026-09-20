import numpy as np
from typing import Dict, Any, List
import config
from simulation.traffic_generator import TrafficGenerator
from simulation.network import SubstrateNetwork
from simulation.metrics import MetricCalculator

class Simulator:
    """
    Main 5G Network Slicing Simulator Engine.
    Coordinates traffic generation, physical substrate processing, and metric collection.
    """

    def __init__(
        self,
        total_bandwidth_mbps: float = config.DEFAULT_TOTAL_BANDWIDTH,
        total_cpu: float = config.DEFAULT_TOTAL_CPU,
        seed: int = config.DEFAULT_RANDOM_SEED
    ):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.traffic_gen = TrafficGenerator(self.rng)
        self.network = SubstrateNetwork(
            total_bandwidth_mbps=total_bandwidth_mbps,
            total_cpu=total_cpu,
            rng=self.rng
        )

    def run_step(
        self,
        slice_manager,
        traffic_load: str = "medium",
        user_counts: Dict[str, int] = None,
        duration: float = config.DEFAULT_SIMULATION_DURATION
    ) -> List[Dict[str, Any]]:
        """
        Runs one iteration of simulation across all active slices.
        """
        load_factor = config.TRAFFIC_LOAD_LEVELS.get(traffic_load, 1.0)
        
        if user_counts is None:
            user_counts = {
                slice_type: config.SLICE_TRAFFIC_PROFILES[slice_type]["default_users"]
                for slice_type in config.ACTIVE_SLICES
            }

        # 1. Generate traffic demand for each slice
        traffic_demands = {}
        for slice_type in config.ACTIVE_SLICES:
            users = user_counts.get(slice_type, config.SLICE_TRAFFIC_PROFILES[slice_type]["default_users"])
            traffic_demands[slice_type] = self.traffic_gen.generate_slice_traffic(
                slice_type=slice_type,
                num_users=users,
                load_factor=load_factor,
                duration=duration
            )

        # 2. Slice Manager computes resource allocation
        allocations = slice_manager.allocate_resources(traffic_demands, self.network)

        # 3. Simulate traffic transmission over substrate network & collect metrics
        step_results = []
        for slice_type in config.ACTIVE_SLICES:
            demand = traffic_demands[slice_type]
            alloc = allocations[slice_type]
            
            res = self.network.process_slice_traffic(
                slice_type=slice_type,
                traffic=demand,
                allocated_bw_mbps=alloc["allocated_bw_mbps"],
                allocated_cpu=alloc["allocated_cpu"]
            )
            
            formatted = MetricCalculator.format_summary_metrics(res)
            step_results.append(formatted)

        return step_results
