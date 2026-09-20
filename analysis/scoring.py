from typing import Dict, Any
import config

class PerformanceScorer:
    """
    Computes a multi-criteria normalized performance score (0 - 100 scale) for each 5G network slice.
    
    Mathematical Formulation:
    -------------------------
    S_Throughput  = min(1.0, Measured_Throughput / Target_Min_Throughput)
    S_Latency     = max(0.0, 1.0 - (Measured_Latency / (Target_Max_Latency * 2.0)))
    S_PacketLoss  = max(0.0, 1.0 - (Measured_Packet_Loss / (Target_Max_Loss * 2.0)))
    S_Reliability = Measured_Reliability / 100.0
    S_Utilization = Measured_Utilization / 100.0

    Overall Score = 100 * [ w_tp*S_Throughput + w_lat*S_Latency + w_loss*S_PacketLoss + w_rel*S_Reliability + w_util*S_Utilization ]
    """

    def __init__(
        self,
        weights: Dict[str, float] = None,
        sla_requirements: Dict[str, Dict[str, float]] = None
    ):
        self.weights = weights if weights is not None else config.SCORING_WEIGHTS
        self.sla_reqs = sla_requirements if sla_requirements is not None else config.SLA_REQUIREMENTS

    def calculate_score(self, metrics: Dict[str, Any]) -> float:
        slice_type = metrics["slice_type"]
        reqs = self.sla_reqs.get(slice_type, config.SLA_REQUIREMENTS[config.SLICE_EMBB])

        # 1. Throughput sub-score (Higher is better)
        target_tp = max(0.1, reqs["min_throughput_mbps"])
        s_tp = min(1.0, metrics["throughput_mbps"] / target_tp)

        # 2. Latency sub-score (Lower is better)
        target_lat = max(1.0, reqs["max_latency_ms"])
        s_lat = max(0.0, 1.0 - (metrics["latency_ms"] / (target_lat * 2.0)))

        # 3. Packet Loss sub-score (Lower is better)
        target_loss = max(0.1, reqs["max_packet_loss_pct"])
        s_loss = max(0.0, 1.0 - (metrics["packet_loss_pct"] / (target_loss * 2.0)))

        # 4. Reliability sub-score (Higher is better)
        s_rel = min(1.0, max(0.0, metrics["reliability_pct"] / 100.0))

        # 5. Resource Utilization sub-score (Efficient utilization between 50%-95%)
        util = metrics["resource_utilization_pct"]
        s_util = min(1.0, max(0.0, util / 100.0))

        # Weighted aggregate
        score = 100.0 * (
            self.weights["throughput"] * s_tp +
            self.weights["latency"] * s_lat +
            self.weights["packet_loss"] * s_loss +
            self.weights["reliability"] * s_rel +
            self.weights["resource_utilization"] * s_util
        )

        return round(max(0.0, min(100.0, score)), 2)
