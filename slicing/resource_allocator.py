from abc import ABC, abstractmethod
from typing import Dict, Any
import config

class BaseResourceAllocator(ABC):
    """
    Abstract Base Class for 5G Network Slice Resource Allocation Strategies.
    """

    @abstractmethod
    def allocate(
        self,
        demands: Dict[str, Dict[str, Any]],
        total_bandwidth: float,
        total_cpu: float
    ) -> Dict[str, Dict[str, float]]:
        """
        Allocates bandwidth (Mbps) and CPU units to each slice.
        
        Args:
            demands: Dict mapping slice_type -> traffic demand dict.
            total_bandwidth: Physical substrate bandwidth available.
            total_cpu: Physical substrate CPU capacity available.
            
        Returns:
            Dict mapping slice_type -> {"allocated_bw_mbps": float, "allocated_cpu": float}
        """
        pass

    def validate_allocation(
        self,
        allocations: Dict[str, Dict[str, float]],
        total_bandwidth: float,
        total_cpu: float
    ) -> bool:
        """
        Sanity Check: Ensures sum of allocated resources does not exceed substrate limits.
        """
        allocated_bw_sum = sum(alloc["allocated_bw_mbps"] for alloc in allocations.values())
        allocated_cpu_sum = sum(alloc["allocated_cpu"] for alloc in allocations.values())

        if allocated_bw_sum > total_bandwidth + 1e-5:
            raise ValueError(f"Allocation Violation: Allocated Bandwidth ({allocated_bw_sum:.2f} Mbps) exceeds Total Bandwidth ({total_bandwidth:.2f} Mbps).")

        if allocated_cpu_sum > total_cpu + 1e-5:
            raise ValueError(f"Allocation Violation: Allocated CPU ({allocated_cpu_sum:.2f}) exceeds Total CPU ({total_cpu:.2f}).")

        return True
