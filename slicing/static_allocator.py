from typing import Dict, Any
import config
from slicing.resource_allocator import BaseResourceAllocator

class StaticResourceAllocator(BaseResourceAllocator):
    """
    Static Resource Allocator Strategy.
    Resources are fixed for each slice according to predefined configuration ratios
    (e.g., eMBB: 60%, URLLC: 25%, mMTC: 15%).
    Unused bandwidth/CPU in one slice cannot be shared with another slice.
    """

    def __init__(self, ratios: Dict[str, float] = None):
        if ratios is None:
            ratios = config.STATIC_ALLOCATION_RATIOS
        # Normalize ratios if they don't sum to 1.0
        total_ratio = sum(ratios.values())
        self.ratios = {k: v / total_ratio for k, v in ratios.items()}

    def allocate(
        self,
        demands: Dict[str, Dict[str, Any]],
        total_bandwidth: float,
        total_cpu: float
    ) -> Dict[str, Dict[str, float]]:
        allocations = {}
        for slice_type in config.ACTIVE_SLICES:
            ratio = self.ratios.get(slice_type, 0.33)
            allocations[slice_type] = {
                "allocated_bw_mbps": total_bandwidth * ratio,
                "allocated_cpu": total_cpu * ratio
            }
        
        self.validate_allocation(allocations, total_bandwidth, total_cpu)
        return allocations
