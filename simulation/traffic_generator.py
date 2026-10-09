import numpy as np
from typing import Dict, Any, List
import config

class TrafficGenerator:
    """
    Generates realistic 5G traffic for different network slice types.
    - eMBB: High packet size, high bandwidth demand, bursty flow.
    - URLLC: Small packet size, high frequency, strict low latency requirements.
    - mMTC: Very small packet size, large number of connected devices, periodic low data rate.
    """

    def __init__(self, rng: np.random.Generator = None):
        self.rng = rng if rng is not None else np.random.default_rng(config.DEFAULT_RANDOM_SEED)

    def generate_slice_traffic(
        self,
        slice_type: str,
        num_users: int,
        load_factor: float = 1.0,
        duration: float = config.DEFAULT_SIMULATION_DURATION
    ) -> Dict[str, Any]:
        """
        Generates aggregate traffic metrics for a given slice and user load.
        
        Returns:
            Dict containing total_packets, generated_mbps, avg_packet_size_kb,
            arrival_rate_pps, demand_bandwidth_mbps, and request_count.
        """
        profile = config.SLICE_TRAFFIC_PROFILES.get(slice_type, config.SLICE_TRAFFIC_PROFILES[config.SLICE_EMBB])
        
        # Base arrival rate scaled by load factor and user count ratio
        base_arrival = profile["base_arrival_rate"] * load_factor
        packet_size_kb = profile["packet_size_kb"]

        if slice_type == config.SLICE_EMBB:
            # eMBB has bursty video traffic (log-normal distribution for packet sizes / rates)
            packet_size_std = packet_size_kb * 0.2
            effective_packet_size = max(0.1, self.rng.normal(packet_size_kb, packet_size_std))
            # Arrival rate varies per user stream
            total_arrival_rate = base_arrival * num_users * self.rng.uniform(0.85, 1.15)
            
        elif slice_type == config.SLICE_URLLC:
            # URLLC has small, steady, high-priority control packets
            effective_packet_size = float(packet_size_kb)
            total_arrival_rate = base_arrival * num_users * self.rng.uniform(0.95, 1.05)
            
        elif slice_type == config.SLICE_MMTC:
            # mMTC has thousands of IoT devices transmitting periodically
            effective_packet_size = float(packet_size_kb)
            # Poisson arrival process for large device counts
            total_arrival_rate = self.rng.poisson(lam=max(1.0, base_arrival * num_users))
        else:
            effective_packet_size = float(packet_size_kb)
            total_arrival_rate = base_arrival * num_users

        # Calculate demand bandwidth (Mbps)
        # arrival_rate (packets/sec) * packet_size (kb/packet) * 8 (bits/byte) / 1000 => Mbps (since 1 kb = 1000 bytes = 8000 bits)
        # Or: arrival_rate_pps * (packet_size_kb * 1000 * 8) / 1,000,000 Mbps = (arrival_rate * packet_size_kb * 8) / 1000.0
        generated_mbps = (total_arrival_rate * effective_packet_size * 8.0) / 1000.0
        
        # Requests generated during simulation duration
        total_packets = int(total_arrival_rate * duration)
        
        return {
            "slice_type": slice_type,
            "num_users": num_users,
            "duration": duration,
            "load_factor": load_factor,
            "arrival_rate_pps": total_arrival_rate,
            "packet_size_kb": effective_packet_size,
            "generated_mbps": generated_mbps,
            "total_packets": total_packets,
            "priority": profile["priority_weight"]
        }
