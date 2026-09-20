import os

# Base Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "generated")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
PLOTS_DIR = os.path.join(RESULTS_DIR, "plots")
CSV_DIR = os.path.join(RESULTS_DIR, "csv")
REPORTS_DIR = os.path.join(RESULTS_DIR, "reports")

# Ensure required directories exist
for directory in [DATA_DIR, RESULTS_DIR, PLOTS_DIR, CSV_DIR, REPORTS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Default Simulation Parameters
DEFAULT_RANDOM_SEED = 42
DEFAULT_SIMULATION_DURATION = 60.0  # seconds
DEFAULT_TOTAL_BANDWIDTH = 100.0  # Mbps
DEFAULT_TOTAL_CPU = 100.0  # CPU Units / Processing capacity (req/s capability)

# Slice Types
SLICE_EMBB = "eMBB"
SLICE_URLLC = "URLLC"
SLICE_MMTC = "mMTC"

ACTIVE_SLICES = [SLICE_EMBB, SLICE_URLLC, SLICE_MMTC]

# Default Static Allocation Ratios
STATIC_ALLOCATION_RATIOS = {
    SLICE_EMBB: 0.60,
    SLICE_URLLC: 0.25,
    SLICE_MMTC: 0.15
}

# SLA Requirements (Configurable Simulation Assumptions)
SLA_REQUIREMENTS = {
    SLICE_EMBB: {
        "min_throughput_mbps": 40.0,
        "max_latency_ms": 100.0,
        "max_packet_loss_pct": 5.0,
        "min_reliability_pct": 95.0
    },
    SLICE_URLLC: {
        "min_throughput_mbps": 3.0,
        "max_latency_ms": 10.0,
        "max_packet_loss_pct": 0.1,
        "min_reliability_pct": 99.9
    },
    SLICE_MMTC: {
        "min_throughput_mbps": 2.0,
        "max_latency_ms": 500.0,
        "max_packet_loss_pct": 5.0,
        "min_reliability_pct": 95.0
    }
}

# Traffic Profiles & Demand Configurations
# Multipliers for traffic load levels
TRAFFIC_LOAD_LEVELS = {
    "low": 0.5,
    "medium": 1.0,
    "high": 1.8,
    "congested": 2.5
}

# Baseline Slice Traffic Characteristics
SLICE_TRAFFIC_PROFILES = {
    SLICE_EMBB: {
        "description": "Enhanced Mobile Broadband - Video streaming & large file transfers",
        "default_users": 50,
        "packet_size_kb": 1.2,       # 1200 Bytes per packet = 1.2 KB
        "base_arrival_rate": 100.0, # Packets / sec / user
        "base_bandwidth_mbps": 50.0,
        "priority_weight": 2
    },
    SLICE_URLLC: {
        "description": "Ultra-Reliable Low-Latency Communication - Autonomous vehicles & remote surgery",
        "default_users": 30,
        "packet_size_kb": 0.10,     # 100 Bytes per packet = 0.10 KB
        "base_arrival_rate": 200.0, # High frequency low delay transmission
        "base_bandwidth_mbps": 20.0,
        "priority_weight": 5        # Highest priority
    },
    SLICE_MMTC: {
        "description": "Massive Machine Type Communications - Smart city sensors & IoT devices",
        "default_users": 500,
        "packet_size_kb": 0.10,     # 100 Bytes per packet = 0.10 KB
        "base_arrival_rate": 5.0,   # Periodic low rate per device
        "base_bandwidth_mbps": 10.0,
        "priority_weight": 1        # Lower priority
    }
}

# Performance Scoring Weights (Must sum to 1.0)
SCORING_WEIGHTS = {
    "throughput": 0.25,
    "latency": 0.25,
    "packet_loss": 0.20,
    "reliability": 0.15,
    "resource_utilization": 0.15
}
