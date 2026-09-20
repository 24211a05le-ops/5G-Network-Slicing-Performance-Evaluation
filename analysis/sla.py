from typing import Dict, Any
import config

class SLAEvaluator:
    """
    Evaluates Service Level Agreement (SLA) satisfaction for 5G network slices.
    """

    def __init__(self, requirements: Dict[str, Dict[str, float]] = None):
        self.requirements = requirements if requirements is not None else config.SLA_REQUIREMENTS

    def evaluate_slice_sla(self, slice_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates SLA conditions for a given slice result.
        
        Checks:
        1. Throughput >= min_throughput_mbps
        2. Latency <= max_latency_ms
        3. Packet Loss <= max_packet_loss_pct
        4. Reliability >= min_reliability_pct
        
        Returns:
            Dict containing sla_satisfied (bool), sla_satisfaction_pct (float), and individual breach flags.
        """
        slice_type = slice_metrics["slice_type"]
        reqs = self.requirements.get(slice_type, config.SLA_REQUIREMENTS[config.SLICE_EMBB])

        throughput_ok = slice_metrics["throughput_mbps"] >= reqs["min_throughput_mbps"]
        latency_ok = slice_metrics["latency_ms"] <= reqs["max_latency_ms"]
        loss_ok = slice_metrics["packet_loss_pct"] <= reqs["max_packet_loss_pct"]
        reliability_ok = slice_metrics["reliability_pct"] >= reqs["min_reliability_pct"]

        passed_checks = sum([throughput_ok, latency_ok, loss_ok, reliability_ok])
        total_checks = 4
        sla_satisfaction_pct = (passed_checks / total_checks) * 100.0
        sla_satisfied = (passed_checks == total_checks)

        return {
            "slice_type": slice_type,
            "sla_satisfied": sla_satisfied,
            "sla_satisfaction_pct": sla_satisfaction_pct,
            "checks": {
                "throughput_ok": throughput_ok,
                "latency_ok": latency_ok,
                "loss_ok": loss_ok,
                "reliability_ok": reliability_ok
            },
            "sla_targets": reqs
        }
