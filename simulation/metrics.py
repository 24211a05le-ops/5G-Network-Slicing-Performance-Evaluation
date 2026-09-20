from typing import Dict, Any

class MetricCalculator:
    """
    Computes standard performance metrics for network slicing experiments and validates sanity constraints.
    
    Formulas:
    1. Throughput (Mbps): (Total Bytes Transmitted * 8) / (Time Duration * 10^6)
    2. End-to-End Latency (ms): T_prop + T_tx + T_proc + T_queue + Jitter
    3. Packet Loss (%): (Total Dropped Packets / Total Packets Generated) * 100
    4. Jitter (ms): Standard deviation / variance of inter-packet arrival delay
    5. Resource Utilization (%): (Demanded Resources / Allocated Resources) * 100
    6. Reliability (%): 100 - Packet Loss (%)
    7. SLA Satisfaction: Evaluates if slice metrics satisfy slice-specific SLA thresholds
    """

    @staticmethod
    def validate_metrics(metrics: Dict[str, Any]) -> bool:
        """
        Performs sanity checks on calculated metrics.
        Raises ValueError if metrics violate physical constraints.
        """
        if metrics.get("throughput_mbps", 0.0) < 0:
            raise ValueError(f"Invalid Throughput: {metrics['throughput_mbps']} Mbps cannot be negative.")
            
        if metrics.get("latency_ms", 0.0) < 0:
            raise ValueError(f"Invalid Latency: {metrics['latency_ms']} ms cannot be negative.")
            
        loss = metrics.get("packet_loss_pct", 0.0)
        if loss < 0.0 or loss > 100.0:
            raise ValueError(f"Invalid Packet Loss: {loss}% must be between 0 and 100%.")

        reliability = metrics.get("reliability_pct", 100.0)
        if reliability < 0.0 or reliability > 100.0:
            raise ValueError(f"Invalid Reliability: {reliability}% must be between 0 and 100%.")

        return True

    @staticmethod
    def format_summary_metrics(raw_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formats raw metrics into a clean dictionary and runs sanity verification.
        """
        formatted = {
            "slice_type": raw_metrics["slice_type"],
            "demand_mbps": round(raw_metrics["demand_mbps"], 2),
            "allocated_bw_mbps": round(raw_metrics["allocated_bw_mbps"], 2),
            "allocated_cpu": round(raw_metrics["allocated_cpu"], 2),
            "throughput_mbps": round(raw_metrics["throughput_mbps"], 2),
            "latency_ms": round(raw_metrics["latency_ms"], 2),
            "jitter_ms": round(raw_metrics["jitter_ms"], 2),
            "packet_loss_pct": round(raw_metrics["packet_loss_pct"], 2),
            "reliability_pct": round(raw_metrics["reliability_pct"], 2),
            "resource_utilization_pct": round(raw_metrics["resource_utilization_pct"], 2),
            "served_packets": raw_metrics["served_packets"],
            "dropped_packets": raw_metrics["dropped_packets"],
            "total_packets": raw_metrics["total_packets"]
        }
        
        MetricCalculator.validate_metrics(formatted)
        return formatted
