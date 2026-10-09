"""
allocation_audit.py
-------------------
Computes a complete, per-slice and aggregate resource allocation audit table.

Terminology used throughout this module:
  demand_bw_mbps       - Bandwidth requested by slice traffic model (Mbps)
  allocated_bw_mbps    - Bandwidth physically reserved for this slice by the allocator (Mbps)
  consumed_bw_mbps     - Bandwidth actually carried (= throughput_mbps from network model)
  unused_bw_mbps       - allocated_bw_mbps - consumed_bw_mbps  (slack within the slice)
  unallocated_bw_mbps  - total_bw - sum(allocated_bw_mbps)  (substrate-level leftover)

CPU quantities follow the same pattern, with CPU units instead of Mbps.
CPU consumption is modelled as:  consumed_cpu = allocated_cpu * (consumed_bw / allocated_bw)
when allocated_bw > 0, else 0.  This is consistent with the 1-CPU-unit-per-Mbps mapping
defined in SubstrateNetwork.process_slice_traffic.
"""

from __future__ import annotations
from typing import List, Dict, Any

import pandas as pd
import config


class AllocationAuditor:
    """
    Builds a detailed resource allocation audit table for one simulation step.

    Input
    -----
    step_metrics : list of dicts returned by MetricCalculator.format_summary_metrics()
                   (one dict per active slice).
    allocations  : dict returned by a resource allocator, keyed by slice type.
                   { slice_type: {"allocated_bw_mbps": float, "allocated_cpu": float} }
    total_bw     : total substrate bandwidth (Mbps)
    total_cpu    : total substrate CPU capacity (units)
    traffic_condition : label string, e.g. "high"
    strategy     : "static" or "dynamic"
    duration_s   : simulation duration in seconds
    seed         : random seed used
    user_counts  : dict { slice_type: int }
    """

    def build_audit_table(
        self,
        step_metrics: List[Dict[str, Any]],
        allocations: Dict[str, Dict[str, float]],
        total_bw: float,
        total_cpu: float,
        traffic_condition: str = "medium",
        strategy: str = "dynamic",
        duration_s: float = 60.0,
        seed: int = 42,
        user_counts: Dict[str, int] = None,
    ) -> pd.DataFrame:
        """
        Returns a DataFrame with one row per slice plus one TOTAL summary row.
        """
        if user_counts is None:
            user_counts = {s: config.SLICE_TRAFFIC_PROFILES[s]["default_users"]
                           for s in config.ACTIVE_SLICES}

        rows = []
        sum_alloc_bw = 0.0
        sum_consumed_bw = 0.0
        sum_alloc_cpu = 0.0
        sum_consumed_cpu = 0.0

        for m in step_metrics:
            stype = m["slice_type"]
            alloc_bw = allocations[stype]["allocated_bw_mbps"]
            alloc_cpu = allocations[stype]["allocated_cpu"]
            demand_bw = m["demand_mbps"]
            consumed_bw = m["throughput_mbps"]          # actual delivered Mbps

            # CPU consumption modelled proportionally to bandwidth service ratio
            if alloc_bw > 1e-9:
                bw_service_ratio = min(1.0, consumed_bw / alloc_bw)
            else:
                bw_service_ratio = 0.0
            consumed_cpu = alloc_cpu * bw_service_ratio

            unused_bw = max(0.0, alloc_bw - consumed_bw)
            unused_cpu = max(0.0, alloc_cpu - consumed_cpu)

            bw_alloc_pct = (alloc_bw / max(1e-9, total_bw)) * 100.0
            bw_util_pct = (consumed_bw / max(1e-9, alloc_bw)) * 100.0
            cpu_util_pct = (consumed_cpu / max(1e-9, alloc_cpu)) * 100.0

            rows.append({
                "Slice": stype,
                "Users/Devices": user_counts.get(stype, 0),
                "Traffic Condition": traffic_condition,
                "Strategy": strategy,
                "Duration (s)": duration_s,
                "Seed": seed,
                # Bandwidth columns
                "BW Demand (Mbps)": round(demand_bw, 3),
                "BW Allocated (Mbps)": round(alloc_bw, 3),
                "BW Consumed (Mbps)": round(consumed_bw, 3),
                "BW Unused (Mbps)": round(unused_bw, 3),
                "BW Alloc % of Total": round(bw_alloc_pct, 2),
                "BW Utilization %": round(min(100.0, bw_util_pct), 2),
                # CPU columns
                "CPU Allocated (units)": round(alloc_cpu, 3),
                "CPU Consumed (units)": round(consumed_cpu, 3),
                "CPU Unused (units)": round(unused_cpu, 3),
                "CPU Utilization %": round(min(100.0, cpu_util_pct), 2),
                # Packet accounting
                "Total Packets": m["total_packets"],
                "Served Packets": m["served_packets"],
                "Dropped Packets": m["dropped_packets"],
                "Packet Loss %": round(m["packet_loss_pct"], 3),
                "Reliability %": round(m["reliability_pct"], 3),
            })

            sum_alloc_bw += alloc_bw
            sum_consumed_bw += consumed_bw
            sum_alloc_cpu += alloc_cpu
            sum_consumed_cpu += consumed_cpu

        unallocated_bw = max(0.0, total_bw - sum_alloc_bw)
        remaining_cpu = max(0.0, total_cpu - sum_alloc_cpu)

        # TOTAL summary row
        rows.append({
            "Slice": "TOTAL",
            "Users/Devices": sum(user_counts.values()),
            "Traffic Condition": traffic_condition,
            "Strategy": strategy,
            "Duration (s)": duration_s,
            "Seed": seed,
            "BW Demand (Mbps)": round(sum(m["demand_mbps"] for m in step_metrics), 3),
            "BW Allocated (Mbps)": round(sum_alloc_bw, 3),
            "BW Consumed (Mbps)": round(sum_consumed_bw, 3),
            "BW Unused (Mbps)": round(sum_alloc_bw - sum_consumed_bw, 3),
            "BW Alloc % of Total": round((sum_alloc_bw / max(1e-9, total_bw)) * 100.0, 2),
            "BW Utilization %": round((sum_consumed_bw / max(1e-9, total_bw)) * 100.0, 2),
            "CPU Allocated (units)": round(sum_alloc_cpu, 3),
            "CPU Consumed (units)": round(sum_consumed_cpu, 3),
            "CPU Unused (units)": round(sum_alloc_cpu - sum_consumed_cpu, 3),
            "CPU Utilization %": round((sum_consumed_cpu / max(1e-9, total_cpu)) * 100.0, 2),
            "Total Packets": sum(m["total_packets"] for m in step_metrics),
            "Served Packets": sum(m["served_packets"] for m in step_metrics),
            "Dropped Packets": sum(m["dropped_packets"] for m in step_metrics),
            "Packet Loss %": round(
                sum(m["dropped_packets"] for m in step_metrics)
                / max(1, sum(m["total_packets"] for m in step_metrics)) * 100.0, 3),
            "Reliability %": round(100.0 - (
                sum(m["dropped_packets"] for m in step_metrics)
                / max(1, sum(m["total_packets"] for m in step_metrics)) * 100.0), 3),
        })

        df = pd.DataFrame(rows)

        # Aggregate scalars returned separately for the dashboard summary banner
        self._last_substrate = {
            "total_bw": total_bw,
            "sum_alloc_bw": round(sum_alloc_bw, 3),
            "sum_consumed_bw": round(sum_consumed_bw, 3),
            "unallocated_bw": round(unallocated_bw, 3),
            "total_cpu": total_cpu,
            "sum_alloc_cpu": round(sum_alloc_cpu, 3),
            "sum_consumed_cpu": round(sum_consumed_cpu, 3),
            "remaining_cpu": round(remaining_cpu, 3),
        }
        return df

    def substrate_summary(self) -> Dict[str, float]:
        """Returns the last-computed substrate-level aggregate metrics."""
        return getattr(self, "_last_substrate", {})
