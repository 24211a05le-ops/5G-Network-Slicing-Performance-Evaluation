import numpy as np
from typing import Dict, Any
import config

class SubstrateNetwork:
    """
    Models the shared physical 5G infrastructure.
    Includes total available bandwidth, total CPU processing capacity, base propagation delay,
    and queuing dynamics.
    """

    def __init__(
        self,
        total_bandwidth_mbps: float = config.DEFAULT_TOTAL_BANDWIDTH,
        total_cpu: float = config.DEFAULT_TOTAL_CPU,
        base_propagation_delay_ms: float = 2.0,
        rng: np.random.Generator = None
    ):
        self.total_bandwidth = float(total_bandwidth_mbps)
        self.total_cpu = float(total_cpu)
        self.base_propagation_delay_ms = float(base_propagation_delay_ms)
        self.rng = rng if rng is not None else np.random.default_rng(config.DEFAULT_RANDOM_SEED)

    def process_slice_traffic(
        self,
        slice_type: str,
        traffic: Dict[str, Any],
        allocated_bw_mbps: float,
        allocated_cpu: float
    ) -> Dict[str, Any]:
        """
        Simulates the transmission and processing of slice traffic through allocated physical resources.
        Returns slice performance raw measurements: served_packets, dropped_packets, throughput, latency, jitter, loss.
        """
        demand_mbps = traffic["generated_mbps"]
        total_packets = traffic["total_packets"]
        arrival_rate = traffic["arrival_rate_pps"]
        duration = traffic["duration"]
        priority = traffic["priority"]
        
        # 1. Throughput & Packet Drop / Service calculation
        # Effective capacity constraint based on allocated bandwidth and allocated CPU processing capability
        cpu_capacity_mbps = allocated_cpu * 1.0  # 1 CPU unit handles ~1 Mbps equivalent load
        effective_capacity_mbps = min(allocated_bw_mbps, cpu_capacity_mbps)
        
        if demand_mbps <= 0:
            served_ratio = 1.0
            throughput_mbps = 0.0
        else:
            # Over-demand leads to bottleneck queue drop
            served_ratio = min(1.0, effective_capacity_mbps / demand_mbps)
            # Add stochastic wireless channel fading/noise effect
            fading_factor = self.rng.uniform(0.98, 1.0)
            throughput_mbps = demand_mbps * served_ratio * fading_factor

        served_packets = int(total_packets * served_ratio)
        dropped_packets = total_packets - served_packets

        # Packet Loss Percentage
        if total_packets > 0:
            packet_loss_pct = ((total_packets - served_packets) / total_packets) * 100.0
        else:
            packet_loss_pct = 0.0

        # URLLC slice special reliability boost under sufficient allocation
        if slice_type == config.SLICE_URLLC and allocated_bw_mbps >= demand_mbps:
            # Highly resilient channel encoding (HARQ / packet duplication)
            packet_loss_pct = max(0.01, packet_loss_pct * 0.05)

        # 2. Latency calculation (End-to-End Latency in milliseconds)
        # Latency = Propagation Delay + Transmission Delay + Queuing Delay + Processing Delay
        # Transmission delay: packet_size / allocated_bandwidth
        packet_size_bits = traffic["packet_size_kb"] * 8.0 * 1024.0
        bw_bps = max(1e-3, allocated_bw_mbps * 1e6)
        tx_delay_ms = (packet_size_bits / bw_bps) * 1000.0

        # Processing delay inversely proportional to allocated CPU
        proc_delay_ms = (10.0 / max(0.1, allocated_cpu))

        # Queuing delay depends on link utilization (M/M/1 queuing model representation)
        utilization = min(0.99, demand_mbps / max(1e-3, allocated_bw_mbps))
        if utilization < 1.0:
            queue_delay_ms = (utilization / (1.0 - utilization)) * 1.5
        else:
            # Under congestion, queue delay explodes up to buffer timeout limits
            queue_delay_ms = 150.0 + (utilization - 1.0) * 200.0

        # URLLC prioritization gives queue bypass / preemption latency reduction
        if slice_type == config.SLICE_URLLC:
            queue_delay_ms *= 0.1
            proc_delay_ms *= 0.2

        # Jitter variation
        jitter_std = max(0.1, queue_delay_ms * 0.15)
        jitter_ms = abs(self.rng.normal(0, jitter_std))

        total_latency_ms = self.base_propagation_delay_ms + tx_delay_ms + proc_delay_ms + queue_delay_ms + jitter_ms

        # 3. Reliability Percentage
        reliability_pct = max(0.0, min(100.0, 100.0 - packet_loss_pct))

        # 4. Resource Utilization Percentage
        bw_utilization_pct = min(100.0, (demand_mbps / max(1e-3, allocated_bw_mbps)) * 100.0) if allocated_bw_mbps > 0 else 0.0
        cpu_utilization_pct = min(100.0, (demand_mbps / max(1e-3, allocated_cpu)) * 100.0) if allocated_cpu > 0 else 0.0
        avg_resource_utilization_pct = (bw_utilization_pct + cpu_utilization_pct) / 2.0

        return {
            "slice_type": slice_type,
            "demand_mbps": demand_mbps,
            "allocated_bw_mbps": allocated_bw_mbps,
            "allocated_cpu": allocated_cpu,
            "throughput_mbps": throughput_mbps,
            "latency_ms": total_latency_ms,
            "jitter_ms": jitter_ms,
            "packet_loss_pct": packet_loss_pct,
            "reliability_pct": reliability_pct,
            "resource_utilization_pct": avg_resource_utilization_pct,
            "served_packets": served_packets,
            "dropped_packets": dropped_packets,
            "total_packets": total_packets
        }
