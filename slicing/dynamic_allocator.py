from typing import Dict, Any
import config
from slicing.resource_allocator import BaseResourceAllocator

class DynamicResourceAllocator(BaseResourceAllocator):
    """
    Dynamic / Priority-Based Resource Allocator Strategy.
    - Dynamically adapts allocations based on real-time slice traffic demand.
    - URLLC has top priority and gets guaranteed minimal allocation + priority preemption under congestion.
    - Unused resources from under-utilized slices are dynamically reallocated to overloaded slices.
    """

    def __init__(self, guaranteed_urllc_pct: float = 0.20):
        self.guaranteed_urllc_pct = guaranteed_urllc_pct

    def allocate(
        self,
        demands: Dict[str, Dict[str, Any]],
        total_bandwidth: float,
        total_cpu: float
    ) -> Dict[str, Dict[str, float]]:
        
        # Extract bandwidth demands
        requested_bw = {
            slice_type: max(0.0, demands.get(slice_type, {}).get("generated_mbps", 0.0))
            for slice_type in config.ACTIVE_SLICES
        }
        
        total_demand = sum(requested_bw.values())
        urllc_demand = requested_bw.get(config.SLICE_URLLC, 0.0)
        embb_demand = requested_bw.get(config.SLICE_EMBB, 0.0)
        mmtc_demand = requested_bw.get(config.SLICE_MMTC, 0.0)

        if total_demand <= total_bandwidth:
            # Under normal load: satisfy each slice's demand + headroom, then distribute remaining capacity proportionally
            base_alloc = {}
            for stype in config.ACTIVE_SLICES:
                # Minimum allocation to guarantee basic SLA targets
                min_bw = config.SLA_REQUIREMENTS[stype]["min_throughput_mbps"] * 0.5
                d = requested_bw[stype]
                base_alloc[stype] = max(min_bw, d * 1.05)

            sum_base = sum(base_alloc.values())
            if sum_base <= total_bandwidth:
                leftover = total_bandwidth - sum_base
                # Distribute leftover according to priority weight * demand (or profile priority)
                weights = {}
                for stype in config.ACTIVE_SLICES:
                    pw = config.SLICE_TRAFFIC_PROFILES[stype]["priority_weight"]
                    weights[stype] = pw * max(1.0, requested_bw[stype])
                sum_weights = sum(weights.values())
                
                allocations = {
                    stype: {"allocated_bw_mbps": base_alloc[stype] + leftover * (weights[stype] / sum_weights)}
                    for stype in config.ACTIVE_SLICES
                }
            else:
                # Scale proportionally if base_alloc exceeds total_bandwidth
                allocations = {
                    stype: {"allocated_bw_mbps": total_bandwidth * (base_alloc[stype] / sum_base)}
                    for stype in config.ACTIVE_SLICES
                }
        else:
            # Under congestion: URLLC has top priority (guarantee 100% of demand or up to 40% of substrate)
            urllc_bw = min(total_bandwidth * 0.40, max(config.SLA_REQUIREMENTS[config.SLICE_URLLC]["min_throughput_mbps"], urllc_demand * 1.05))
            remaining_bw = max(0.0, total_bandwidth - urllc_bw)

            embb_pw = config.SLICE_TRAFFIC_PROFILES[config.SLICE_EMBB]["priority_weight"]
            mmtc_pw = config.SLICE_TRAFFIC_PROFILES[config.SLICE_MMTC]["priority_weight"]

            embb_w = max(0.1, embb_demand) * embb_pw
            mmtc_w = max(0.1, mmtc_demand) * mmtc_pw
            tot_w = embb_w + mmtc_w

            embb_bw = remaining_bw * (embb_w / tot_w)
            mmtc_bw = remaining_bw * (mmtc_w / tot_w)

            allocations = {
                config.SLICE_EMBB: {"allocated_bw_mbps": embb_bw},
                config.SLICE_URLLC: {"allocated_bw_mbps": urllc_bw},
                config.SLICE_MMTC: {"allocated_bw_mbps": mmtc_bw}
            }

        # CPU Allocation proportional to allocated bandwidth
        for slice_type in config.ACTIVE_SLICES:
            fraction = allocations[slice_type]["allocated_bw_mbps"] / total_bandwidth
            allocations[slice_type]["allocated_cpu"] = total_cpu * fraction

        self.validate_allocation(allocations, total_bandwidth, total_cpu)
        return allocations
