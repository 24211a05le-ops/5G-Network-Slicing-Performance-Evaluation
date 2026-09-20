from typing import Dict, Any
import config
from slicing.static_allocator import StaticResourceAllocator
from slicing.dynamic_allocator import DynamicResourceAllocator

class SliceManager:
    """
    5G Network Slice Manager.
    - Manages slice lifecycle and active slice profiles.
    - Selects resource allocation policy (Static vs Dynamic).
    """

    def __init__(self, strategy: str = "dynamic"):
        self.strategy_name = strategy.lower()
        if self.strategy_name == "static":
            self.allocator = StaticResourceAllocator()
        else:
            self.allocator = DynamicResourceAllocator()

    def set_strategy(self, strategy: str):
        self.strategy_name = strategy.lower()
        if self.strategy_name == "static":
            self.allocator = StaticResourceAllocator()
        else:
            self.allocator = DynamicResourceAllocator()

    def allocate_resources(
        self,
        traffic_demands: Dict[str, Dict[str, Any]],
        substrate_network
    ) -> Dict[str, Dict[str, float]]:
        """
        Delegates allocation calculation to the active allocation strategy.
        """
        return self.allocator.allocate(
            demands=traffic_demands,
            total_bandwidth=substrate_network.total_bandwidth,
            total_cpu=substrate_network.total_cpu
        )
