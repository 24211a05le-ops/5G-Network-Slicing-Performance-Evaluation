"""
test_allocation_invariants.py
------------------------------
Automated tests verifying every allocation invariant for both static and dynamic
strategies across every supported traffic condition.

Baseline inputs (matching the audit specification):
  total_bw  = 100 Mbps
  total_cpu = 100 units
  eMBB  users = 50
  URLLC users = 30
  mMTC devices = 500
  seed = 42
"""

import pytest
import numpy as np
import config
from simulation.simulator import Simulator
from slicing.slice_manager import SliceManager
from slicing.static_allocator import StaticResourceAllocator
from slicing.dynamic_allocator import DynamicResourceAllocator
from simulation.traffic_generator import TrafficGenerator
from simulation.network import SubstrateNetwork
from analysis.allocation_audit import AllocationAuditor
from analysis.sla import SLAEvaluator

# ─── Fixtures ────────────────────────────────────────────────────────────────

TOTAL_BW = 100.0
TOTAL_CPU = 100.0
SEED = 42
USER_COUNTS = {
    config.SLICE_EMBB:  50,
    config.SLICE_URLLC: 30,
    config.SLICE_MMTC:  500,
}
TRAFFIC_CONDITIONS = ["low", "medium", "high", "congested"]
STRATEGIES = ["static", "dynamic"]


def _run_one(strategy: str, traffic: str):
    """Run one simulation step; return (step_metrics, allocations, network)."""
    sim = Simulator(total_bandwidth_mbps=TOTAL_BW, total_cpu=TOTAL_CPU, seed=SEED)
    sm = SliceManager(strategy)
    load = config.TRAFFIC_LOAD_LEVELS[traffic]

    tg = TrafficGenerator(sim.rng)
    demands = {}
    for stype in config.ACTIVE_SLICES:
        demands[stype] = tg.generate_slice_traffic(
            slice_type=stype,
            num_users=USER_COUNTS[stype],
            load_factor=load,
            duration=60.0,
        )

    allocations = sm.allocate_resources(demands, sim.network)

    step_metrics = []
    for stype in config.ACTIVE_SLICES:
        raw = sim.network.process_slice_traffic(
            slice_type=stype,
            traffic=demands[stype],
            allocated_bw_mbps=allocations[stype]["allocated_bw_mbps"],
            allocated_cpu=allocations[stype]["allocated_cpu"],
        )
        step_metrics.append(raw)

    return step_metrics, allocations


# ─── Section 1: Bandwidth Constraints ────────────────────────────────────────

@pytest.mark.parametrize("strategy", STRATEGIES)
@pytest.mark.parametrize("traffic", TRAFFIC_CONDITIONS)
def test_all_bw_allocations_non_negative(strategy, traffic):
    _, allocations = _run_one(strategy, traffic)
    for stype, alloc in allocations.items():
        assert alloc["allocated_bw_mbps"] >= 0.0, (
            f"{strategy}/{traffic}: {stype} BW allocation is negative: "
            f"{alloc['allocated_bw_mbps']}"
        )


@pytest.mark.parametrize("strategy", STRATEGIES)
@pytest.mark.parametrize("traffic", TRAFFIC_CONDITIONS)
def test_total_bw_does_not_exceed_substrate(strategy, traffic):
    _, allocations = _run_one(strategy, traffic)
    total_alloc = sum(a["allocated_bw_mbps"] for a in allocations.values())
    assert total_alloc <= TOTAL_BW + 1e-5, (
        f"{strategy}/{traffic}: sum(allocated_bw)={total_alloc:.4f} > {TOTAL_BW}"
    )


@pytest.mark.parametrize("strategy", STRATEGIES)
@pytest.mark.parametrize("traffic", TRAFFIC_CONDITIONS)
def test_consumed_bw_does_not_exceed_allocation(strategy, traffic):
    step_metrics, allocations = _run_one(strategy, traffic)
    for m in step_metrics:
        stype = m["slice_type"]
        alloc_bw = allocations[stype]["allocated_bw_mbps"]
        consumed_bw = m["throughput_mbps"]
        assert consumed_bw <= alloc_bw + 1e-3, (
            f"{strategy}/{traffic}: {stype} consumed_bw={consumed_bw:.4f} > "
            f"alloc_bw={alloc_bw:.4f}"
        )


@pytest.mark.parametrize("strategy", STRATEGIES)
@pytest.mark.parametrize("traffic", TRAFFIC_CONDITIONS)
def test_unallocated_bw_is_non_negative(strategy, traffic):
    _, allocations = _run_one(strategy, traffic)
    total_alloc = sum(a["allocated_bw_mbps"] for a in allocations.values())
    unallocated = TOTAL_BW - total_alloc
    assert unallocated >= -1e-5, (
        f"{strategy}/{traffic}: unallocated BW is negative: {unallocated:.4f}"
    )


# ─── Section 2: CPU Constraints ──────────────────────────────────────────────

@pytest.mark.parametrize("strategy", STRATEGIES)
@pytest.mark.parametrize("traffic", TRAFFIC_CONDITIONS)
def test_all_cpu_allocations_non_negative(strategy, traffic):
    _, allocations = _run_one(strategy, traffic)
    for stype, alloc in allocations.items():
        assert alloc["allocated_cpu"] >= 0.0, (
            f"{strategy}/{traffic}: {stype} CPU allocation is negative"
        )


@pytest.mark.parametrize("strategy", STRATEGIES)
@pytest.mark.parametrize("traffic", TRAFFIC_CONDITIONS)
def test_total_cpu_does_not_exceed_substrate(strategy, traffic):
    _, allocations = _run_one(strategy, traffic)
    total_cpu_alloc = sum(a["allocated_cpu"] for a in allocations.values())
    assert total_cpu_alloc <= TOTAL_CPU + 1e-5, (
        f"{strategy}/{traffic}: sum(allocated_cpu)={total_cpu_alloc:.4f} > {TOTAL_CPU}"
    )


@pytest.mark.parametrize("strategy", STRATEGIES)
@pytest.mark.parametrize("traffic", TRAFFIC_CONDITIONS)
def test_remaining_cpu_non_negative(strategy, traffic):
    _, allocations = _run_one(strategy, traffic)
    total_cpu_alloc = sum(a["allocated_cpu"] for a in allocations.values())
    remaining = TOTAL_CPU - total_cpu_alloc
    assert remaining >= -1e-5, (
        f"{strategy}/{traffic}: remaining CPU negative: {remaining:.4f}"
    )


# ─── Section 3: Demand & Throughput Constraints ───────────────────────────────

@pytest.mark.parametrize("strategy", STRATEGIES)
@pytest.mark.parametrize("traffic", TRAFFIC_CONDITIONS)
def test_throughput_does_not_exceed_demand(strategy, traffic):
    """Delivered throughput must never exceed what was offered."""
    step_metrics, _ = _run_one(strategy, traffic)
    for m in step_metrics:
        assert m["throughput_mbps"] <= m["demand_mbps"] + 1e-3, (
            f"{strategy}/{traffic}: {m['slice_type']} throughput "
            f"{m['throughput_mbps']:.4f} > demand {m['demand_mbps']:.4f}"
        )


@pytest.mark.parametrize("strategy", STRATEGIES)
@pytest.mark.parametrize("traffic", TRAFFIC_CONDITIONS)
def test_served_plus_dropped_equals_total_packets(strategy, traffic):
    step_metrics, _ = _run_one(strategy, traffic)
    for m in step_metrics:
        assert m["served_packets"] + m["dropped_packets"] == m["total_packets"], (
            f"{strategy}/{traffic}: {m['slice_type']} served+dropped != total"
        )


@pytest.mark.parametrize("strategy", STRATEGIES)
@pytest.mark.parametrize("traffic", TRAFFIC_CONDITIONS)
def test_packet_loss_reliability_sum_to_100(strategy, traffic):
    step_metrics, _ = _run_one(strategy, traffic)
    for m in step_metrics:
        total = m["packet_loss_pct"] + m["reliability_pct"]
        assert abs(total - 100.0) < 1e-3, (
            f"{strategy}/{traffic}: {m['slice_type']} "
            f"loss+reliability={total:.4f} != 100"
        )


# ─── Section 4: Utilization Constraints ──────────────────────────────────────

@pytest.mark.parametrize("strategy", STRATEGIES)
@pytest.mark.parametrize("traffic", TRAFFIC_CONDITIONS)
def test_utilization_pct_bounds(strategy, traffic):
    step_metrics, _ = _run_one(strategy, traffic)
    for m in step_metrics:
        util = m["resource_utilization_pct"]
        assert 0.0 <= util <= 100.0 + 1e-5, (
            f"{strategy}/{traffic}: {m['slice_type']} utilization={util:.2f}% "
            "out of [0, 100]"
        )


@pytest.mark.parametrize("strategy", STRATEGIES)
@pytest.mark.parametrize("traffic", TRAFFIC_CONDITIONS)
def test_packet_loss_pct_bounds(strategy, traffic):
    step_metrics, _ = _run_one(strategy, traffic)
    for m in step_metrics:
        loss = m["packet_loss_pct"]
        assert 0.0 <= loss <= 100.0 + 1e-5, (
            f"{strategy}/{traffic}: {m['slice_type']} packet_loss={loss:.3f}% out of bounds"
        )


# ─── Section 5: Static-specific invariants ───────────────────────────────────

def test_static_shares_identical_regardless_of_demand():
    """Static allocation must return the same numbers for any demand level."""
    alloc = StaticResourceAllocator()
    low = {s: {"generated_mbps": 0.5} for s in config.ACTIVE_SLICES}
    high = {s: {"generated_mbps": 999.0} for s in config.ACTIVE_SLICES}
    result_low  = alloc.allocate(low,  TOTAL_BW, TOTAL_CPU)
    result_high = alloc.allocate(high, TOTAL_BW, TOTAL_CPU)
    for stype in config.ACTIVE_SLICES:
        assert result_low[stype]["allocated_bw_mbps"] == pytest.approx(
            result_high[stype]["allocated_bw_mbps"], abs=1e-9
        ), f"Static BW differs between demand levels for {stype}"
        assert result_low[stype]["allocated_cpu"] == pytest.approx(
            result_high[stype]["allocated_cpu"], abs=1e-9
        ), f"Static CPU differs between demand levels for {stype}"


def test_static_bw_ratios_correct():
    alloc = StaticResourceAllocator()
    demands = {s: {"generated_mbps": 0.0} for s in config.ACTIVE_SLICES}
    result = alloc.allocate(demands, TOTAL_BW, TOTAL_CPU)
    assert result[config.SLICE_EMBB]["allocated_bw_mbps"] == pytest.approx(60.0, abs=1e-6)
    assert result[config.SLICE_URLLC]["allocated_bw_mbps"] == pytest.approx(25.0, abs=1e-6)
    assert result[config.SLICE_MMTC]["allocated_bw_mbps"] == pytest.approx(15.0, abs=1e-6)


# ─── Section 6: Dynamic-specific invariants ──────────────────────────────────

def test_dynamic_urllc_priority_under_congestion():
    """Under very high load, URLLC should receive >= its SLA minimum throughput."""
    alloc = DynamicResourceAllocator()
    demands = {
        config.SLICE_EMBB:  {"generated_mbps": 500.0},
        config.SLICE_URLLC: {"generated_mbps": 50.0},
        config.SLICE_MMTC:  {"generated_mbps": 200.0},
    }
    result = alloc.allocate(demands, TOTAL_BW, TOTAL_CPU)
    urllc_min = config.SLA_REQUIREMENTS[config.SLICE_URLLC]["min_throughput_mbps"]
    assert result[config.SLICE_URLLC]["allocated_bw_mbps"] >= urllc_min, (
        f"Dynamic URLLC allocation {result[config.SLICE_URLLC]['allocated_bw_mbps']:.3f} "
        f"< SLA minimum {urllc_min}"
    )


def test_dynamic_zero_demand_distributes_resources():
    """With zero traffic, dynamic allocator should still return valid non-negative allocations."""
    alloc = DynamicResourceAllocator()
    demands = {s: {"generated_mbps": 0.0} for s in config.ACTIVE_SLICES}
    result = alloc.allocate(demands, TOTAL_BW, TOTAL_CPU)
    for stype in config.ACTIVE_SLICES:
        assert result[stype]["allocated_bw_mbps"] >= 0.0
        assert result[stype]["allocated_cpu"] >= 0.0
    total = sum(r["allocated_bw_mbps"] for r in result.values())
    assert total <= TOTAL_BW + 1e-5


# ─── Section 7: AllocationAuditor invariants ─────────────────────────────────

@pytest.mark.parametrize("strategy", STRATEGIES)
@pytest.mark.parametrize("traffic", TRAFFIC_CONDITIONS)
def test_audit_table_row_count(strategy, traffic):
    step_metrics, allocations = _run_one(strategy, traffic)
    auditor = AllocationAuditor()
    df = auditor.build_audit_table(
        step_metrics, allocations, TOTAL_BW, TOTAL_CPU,
        traffic_condition=traffic, strategy=strategy,
        user_counts=USER_COUNTS,
    )
    # 3 slice rows + 1 TOTAL row
    assert len(df) == 4, f"Expected 4 rows, got {len(df)}"


@pytest.mark.parametrize("strategy", STRATEGIES)
@pytest.mark.parametrize("traffic", TRAFFIC_CONDITIONS)
def test_audit_total_row_bw_conservation(strategy, traffic):
    step_metrics, allocations = _run_one(strategy, traffic)
    auditor = AllocationAuditor()
    df = auditor.build_audit_table(
        step_metrics, allocations, TOTAL_BW, TOTAL_CPU,
        traffic_condition=traffic, strategy=strategy,
        user_counts=USER_COUNTS,
    )
    total_row = df[df["Slice"] == "TOTAL"].iloc[0]
    slice_rows = df[df["Slice"] != "TOTAL"]

    assert total_row["BW Allocated (Mbps)"] == pytest.approx(
        slice_rows["BW Allocated (Mbps)"].sum(), abs=1e-3
    ), "Audit TOTAL BW allocation does not match sum of slices"

    assert total_row["BW Consumed (Mbps)"] == pytest.approx(
        slice_rows["BW Consumed (Mbps)"].sum(), abs=1e-3
    ), "Audit TOTAL BW consumed does not match sum of slices"


@pytest.mark.parametrize("strategy", STRATEGIES)
@pytest.mark.parametrize("traffic", TRAFFIC_CONDITIONS)
def test_audit_bw_utilization_pct_bounds(strategy, traffic):
    step_metrics, allocations = _run_one(strategy, traffic)
    auditor = AllocationAuditor()
    df = auditor.build_audit_table(
        step_metrics, allocations, TOTAL_BW, TOTAL_CPU,
        traffic_condition=traffic, strategy=strategy,
        user_counts=USER_COUNTS,
    )
    for _, row in df[df["Slice"] != "TOTAL"].iterrows():
        util = row["BW Utilization %"]
        assert 0.0 <= util <= 100.0 + 1e-3, (
            f"{strategy}/{traffic}: {row['Slice']} BW util={util:.2f}% out of bounds"
        )


@pytest.mark.parametrize("strategy", STRATEGIES)
@pytest.mark.parametrize("traffic", TRAFFIC_CONDITIONS)
def test_audit_substrate_summary_conserved(strategy, traffic):
    step_metrics, allocations = _run_one(strategy, traffic)
    auditor = AllocationAuditor()
    auditor.build_audit_table(
        step_metrics, allocations, TOTAL_BW, TOTAL_CPU,
        traffic_condition=traffic, strategy=strategy,
        user_counts=USER_COUNTS,
    )
    s = auditor.substrate_summary()
    assert s["sum_alloc_bw"] + s["unallocated_bw"] == pytest.approx(TOTAL_BW, abs=1e-3), (
        f"BW conservation failed: alloc={s['sum_alloc_bw']} + "
        f"unalloc={s['unallocated_bw']} != {TOTAL_BW}"
    )
    assert s["sum_alloc_cpu"] + s["remaining_cpu"] == pytest.approx(TOTAL_CPU, abs=1e-3), (
        f"CPU conservation failed: alloc={s['sum_alloc_cpu']} + "
        f"remaining={s['remaining_cpu']} != {TOTAL_CPU}"
    )
