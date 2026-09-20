import os
import json
import pandas as pd
from typing import List, Dict, Any
import config
from analysis.sla import SLAEvaluator
from analysis.scoring import PerformanceScorer

class PerformanceEvaluator:
    """
    Evaluates, combines, and exports raw simulation metrics alongside SLA satisfaction and performance scores.
    """

    def __init__(self):
        self.sla_evaluator = SLAEvaluator()
        self.scorer = PerformanceScorer()

    def evaluate_step(
        self,
        step_metrics: List[Dict[str, Any]],
        experiment_id: str = "exp_default",
        traffic_condition: str = "medium",
        allocation_strategy: str = "dynamic",
        users_count: int = 100,
        total_bandwidth: float = config.DEFAULT_TOTAL_BANDWIDTH
    ) -> pd.DataFrame:
        
        evaluated_rows = []
        for m in step_metrics:
            sla_res = self.sla_evaluator.evaluate_slice_sla(m)
            score = self.scorer.calculate_score(m)

            row = {
                "experiment_id": experiment_id,
                "slice_type": m["slice_type"],
                "traffic_condition": traffic_condition,
                "allocation_strategy": allocation_strategy,
                "users": users_count,
                "bandwidth": total_bandwidth,
                "demand_mbps": m["demand_mbps"],
                "allocated_bw_mbps": m["allocated_bw_mbps"],
                "throughput": m["throughput_mbps"],
                "latency": m["latency_ms"],
                "packet_loss": m["packet_loss_pct"],
                "jitter": m["jitter_ms"],
                "reliability": m["reliability_pct"],
                "resource_utilization": m["resource_utilization_pct"],
                "served_requests": m["served_packets"],
                "dropped_requests": m["dropped_packets"],
                "sla_satisfaction": sla_res["sla_satisfaction_pct"],
                "sla_satisfied": sla_res["sla_satisfied"],
                "performance_score": score
            }
            evaluated_rows.append(row)

        return pd.DataFrame(evaluated_rows)

    def export_results(self, df: pd.DataFrame, filename_stem: str = "simulation_results"):
        """
        Saves DataFrame as CSV and JSON files in RESULTS_DIR.
        """
        csv_path = os.path.join(config.CSV_DIR, f"{filename_stem}.csv")
        json_path = os.path.join(config.CSV_DIR, f"{filename_stem}.json")

        df.to_csv(csv_path, index=False)
        df.to_json(json_path, orient="records", indent=2)
        
        return csv_path, json_path
