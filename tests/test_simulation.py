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

def test_zero_offered_traffic():
    rng = np.random.default_rng(42)
    net = SubstrateNetwork(total_bandwidth_mbps=100.0, total_cpu=100.0, rng=rng)
    traffic = {
        "slice_type": config.SLICE_EMBB,
        "num_users": 0,
        "duration": 60.0,
        "load_factor": 0.0,
        "arrival_rate_pps": 0.0,
        "packet_size_kb": 1.2,
        "generated_mbps": 0.0,
        "total_packets": 0,
        "priority": 2.0
    }
    res = net.process_slice_traffic(config.SLICE_EMBB, traffic, allocated_bw_mbps=30.0, allocated_cpu=30.0)
    assert res["throughput_mbps"] == 0.0
    assert res["packet_loss_pct"] == 0.0
    assert res["reliability_pct"] == 100.0

def test_static_shares_fixed_across_demands():
    allocator = StaticResourceAllocator()
    demands_low = {
        config.SLICE_EMBB: {"generated_mbps": 5.0},
        config.SLICE_URLLC: {"generated_mbps": 1.0},
        config.SLICE_MMTC: {"generated_mbps": 0.5}
    }
    demands_high = {
        config.SLICE_EMBB: {"generated_mbps": 200.0},
        config.SLICE_URLLC: {"generated_mbps": 100.0},
        config.SLICE_MMTC: {"generated_mbps": 50.0}
    }
    alloc_low = allocator.allocate(demands_low, 100.0, 100.0)
    alloc_high = allocator.allocate(demands_high, 100.0, 100.0)
    assert alloc_low == alloc_high

def test_resource_limits_never_exceeded():
    allocator = DynamicResourceAllocator()
    demands = {
        config.SLICE_EMBB: {"generated_mbps": 500.0},
        config.SLICE_URLLC: {"generated_mbps": 300.0},
        config.SLICE_MMTC: {"generated_mbps": 200.0}
    }
    allocations = allocator.allocate(demands, total_bandwidth=150.0, total_cpu=150.0)
    tot_bw = sum(a["allocated_bw_mbps"] for a in allocations.values())
    tot_cpu = sum(a["allocated_cpu"] for a in allocations.values())
    assert tot_bw <= 150.0 + 1e-5
    assert tot_cpu <= 150.0 + 1e-5

def test_packet_loss_reliability_consistency():
    rng = np.random.default_rng(42)
    net = SubstrateNetwork(total_bandwidth_mbps=100.0, total_cpu=100.0, rng=rng)
    traffic = {
        "slice_type": config.SLICE_EMBB,
        "num_users": 50,
        "duration": 60.0,
        "load_factor": 3.0,
        "arrival_rate_pps": 1000.0,
        "packet_size_kb": 1.2,
        "generated_mbps": 96.0,
        "total_packets": 60000,
        "priority": 2.0
    }
    res = net.process_slice_traffic(config.SLICE_EMBB, traffic, allocated_bw_mbps=30.0, allocated_cpu=30.0)
    assert pytest.approx(res["reliability_pct"] + res["packet_loss_pct"], abs=1e-3) == 100.0

def test_reproducible_seeded_runs():
    from simulation.simulator import Simulator
    from slicing.slice_manager import SliceManager
    
    sim1 = Simulator(seed=12345)
    sm1 = SliceManager("dynamic")
    res1 = sim1.run_step(sm1, traffic_load="high")

    sim2 = Simulator(seed=12345)
    sm2 = SliceManager("dynamic")
    res2 = sim2.run_step(sm2, traffic_load="high")

    assert res1 == res2

def test_csv_export_matches_simulation_output(tmp_path):
    from analysis.evaluator import PerformanceEvaluator
    evaluator = PerformanceEvaluator()
    step_metrics = [{
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
    }]
    df = evaluator.evaluate_step(step_metrics)
    assert len(df) == 1
    assert df["throughput"].iloc[0] == 48.0
    assert 0.0 <= df["performance_score"].iloc[0] <= 100.0

