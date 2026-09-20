import pytest
import numpy as np
import config
from simulation.traffic_generator import TrafficGenerator
from simulation.network import SubstrateNetwork
from simulation.metrics import MetricCalculator
from slicing.static_allocator import StaticResourceAllocator
from slicing.dynamic_allocator import DynamicResourceAllocator
from analysis.sla import SLAEvaluator
from analysis.scoring import PerformanceScorer

def test_traffic_generation():
    rng = np.random.default_rng(42)
    tg = TrafficGenerator(rng)
    
    embb_traffic = tg.generate_slice_traffic(config.SLICE_EMBB, num_users=50, load_factor=1.0)
    assert embb_traffic["slice_type"] == config.SLICE_EMBB
    assert embb_traffic["generated_mbps"] > 0
    assert embb_traffic["total_packets"] > 0

    urllc_traffic = tg.generate_slice_traffic(config.SLICE_URLLC, num_users=30, load_factor=1.0)
    assert urllc_traffic["slice_type"] == config.SLICE_URLLC
    assert urllc_traffic["generated_mbps"] > 0

    mmtc_traffic = tg.generate_slice_traffic(config.SLICE_MMTC, num_users=500, load_factor=1.0)
    assert mmtc_traffic["slice_type"] == config.SLICE_MMTC
    assert mmtc_traffic["generated_mbps"] > 0

def test_static_resource_allocator():
    allocator = StaticResourceAllocator()
    demands = {
        config.SLICE_EMBB: {"generated_mbps": 50.0},
        config.SLICE_URLLC: {"generated_mbps": 20.0},
        config.SLICE_MMTC: {"generated_mbps": 10.0}
    }
    allocations = allocator.allocate(demands, total_bandwidth=100.0, total_cpu=100.0)
    
    assert allocations[config.SLICE_EMBB]["allocated_bw_mbps"] == pytest.approx(60.0, abs=1e-3)
    assert allocations[config.SLICE_URLLC]["allocated_bw_mbps"] == pytest.approx(25.0, abs=1e-3)
    assert allocations[config.SLICE_MMTC]["allocated_bw_mbps"] == pytest.approx(15.0, abs=1e-3)

def test_dynamic_resource_allocator():
    allocator = DynamicResourceAllocator()
    demands = {
        config.SLICE_EMBB: {"generated_mbps": 100.0},
        config.SLICE_URLLC: {"generated_mbps": 40.0},
        config.SLICE_MMTC: {"generated_mbps": 5.0}
    }
    allocations = allocator.allocate(demands, total_bandwidth=100.0, total_cpu=100.0)
    
    # Sum of allocated bandwidth must not exceed substrate total
    total_allocated_bw = sum(alloc["allocated_bw_mbps"] for alloc in allocations.values())
    assert total_allocated_bw <= 100.0 + 1e-5
    # URLLC should receive high allocation due to high demand
    assert allocations[config.SLICE_URLLC]["allocated_bw_mbps"] >= 20.0

def test_metric_validation_sanity():
    valid_metrics = {
        "slice_type": "eMBB",
        "demand_mbps": 50.0,
        "allocated_bw_mbps": 60.0,
        "allocated_cpu": 60.0,
        "throughput_mbps": 48.0,
        "latency_ms": 25.0,
        "jitter_ms": 3.0,
        "packet_loss_pct": 2.0,
        "reliability_pct": 98.0,
        "resource_utilization_pct": 80.0,
        "served_packets": 1000,
        "dropped_packets": 20,
        "total_packets": 1020
    }
    assert MetricCalculator.validate_metrics(valid_metrics) is True

    invalid_metrics = valid_metrics.copy()
    invalid_metrics["packet_loss_pct"] = 150.0
    with pytest.raises(ValueError):
        MetricCalculator.validate_metrics(invalid_metrics)

def test_sla_evaluator():
    evaluator = SLAEvaluator()
    urllc_good = {
        "slice_type": config.SLICE_URLLC,
        "throughput_mbps": 10.0,
        "latency_ms": 5.0,
        "packet_loss_pct": 0.05,
        "reliability_pct": 99.95
    }
    res_good = evaluator.evaluate_slice_sla(urllc_good)
    assert res_good["sla_satisfied"] is True

    urllc_bad = {
        "slice_type": config.SLICE_URLLC,
        "throughput_mbps": 2.0,
        "latency_ms": 50.0,  # Exceeds max 10ms
        "packet_loss_pct": 2.0,
        "reliability_pct": 98.0
    }
    res_bad = evaluator.evaluate_slice_sla(urllc_bad)
    assert res_bad["sla_satisfied"] is False

def test_performance_scorer():
    scorer = PerformanceScorer()
    metrics = {
        "slice_type": config.SLICE_EMBB,
        "throughput_mbps": 50.0,
        "latency_ms": 30.0,
        "packet_loss_pct": 1.0,
        "reliability_pct": 99.0,
        "resource_utilization_pct": 85.0
    }
    score = scorer.calculate_score(metrics)
    assert 0.0 <= score <= 100.0
    assert score > 70.0
