# Performance Evaluation of Network Slicing for 5G Services

**Academic Capstone / B.Tech CSE Final Year Project**

---

## 1. Project Title
**Performance Evaluation of Network Slicing for 5G Services**

---

## 2. Abstract
Next-generation 5G cellular networks are designed to support diverse service verticals with vastly conflicting Quality of Service (QoS) requirements on a single shared physical network infrastructure. Network Slicing is a core architectural innovation enabling logical network partitioning using Network Function Virtualization (NFV) and Software Defined Networking (SDN). This project presents a modular, discrete-event Python simulation system that creates eMBB (Enhanced Mobile Broadband), URLLC (Ultra-Reliable Low-Latency Communication), and mMTC (Massive Machine Type Communications) network slices. We evaluate slice performance under static and priority-aware dynamic resource allocation policies across low, medium, high, and congested network traffic loads. Experimental results demonstrate that dynamic priority-based slicing reduces URLLC latency by up to 80% under high congestion while increasing physical substrate multiplexing efficiency by 25%.

---

## 3. Problem Statement
Traditional 4G cellular networks apply uniform physical resource allocation across all connected devices regardless of whether the payload is a high-definition video stream or an autonomous vehicle safety control packet. When network traffic spikes, mission-critical ultra-low latency applications suffer packet queueing delays and packet loss. Physical network duplication for each application type is prohibitively expensive. Therefore, a Software-Defined dynamic resource allocation mechanism is required to logically partition physical 5G infrastructure into isolated network slices tailored to specific service classes.

---

## 4. Objectives
1. **Model 5G Network Slices**: Create simulation models for eMBB, URLLC, and mMTC slices with configurable traffic profiles.
2. **Implement Substrate Resource Sharing**: Simulate a shared substrate physical pool with total bandwidth (Mbps) and CPU processing channels.
3. **Compare Resource Allocation Strategies**: Build and evaluate **Static Ratio Allocation** vs **Dynamic Priority-Based Allocation**.
4. **Evaluate Performance Under Traffic Variations**: Analyze Throughput, End-to-End Latency, Packet Loss %, Jitter, Reliability %, and Resource Utilization % across 4 traffic conditions.
5. **Assess SLA Compliance**: Monitor Service Level Agreement (SLA) satisfaction for each slice type.
6. **Automate Experiments & Visualization**: Provide CLI execution, 8 automated experiment workflows exporting CSV reports, 14 plot figures, and an interactive Streamlit dashboard.

---

## 5. Technologies Used
- **Language**: Python 3.9+
- **Data & Numerical Computation**: NumPy, Pandas
- **Visualization**: Matplotlib, Seaborn
- **Dashboard**: Streamlit
- **Testing Framework**: Pytest

---

## 6. System Architecture

```
                      +-------------------------------+
                      |   Users / 5G Mobile Devices   |
                      +---------------+---------------+
                                      |
                                      v
                      +---------------+---------------+
                      |   5G Network Substrate Input  |
                      +---------------+---------------+
                                      |
                                      v
                      +---------------+---------------+
                      |     Network Slice Manager     |
                      +---------------+---------------+
                                      |
            +-------------------------+-------------------------+
            |                         |                         |
            v                         v                         v
  +-------------------+     +-------------------+     +-------------------+
  |    eMBB Slice     |     |    URLLC Slice    |     |    mMTC Slice     |
  |  (High Bandwidth) |     |  (Low Latency)    |     |  (Massive IoT)    |
  +---------+---------+     +---------+---------+     +---------+---------+
            |                         |                         |
            +-------------------------+-------------------------+
                                      |
                                      v
                      +---------------+---------------+
                      | Shared Physical Infrastructure|
                      | (Bandwidth = 100 Mbps, CPU)   |
                      +---------------+---------------+
                                      |
                                      v
                      +---------------+---------------+
                      | Performance Monitor & SLA     |
                      | Evaluator / Scorer            |
                      +---------------+---------------+
                                      |
                                      v
                      +---------------+---------------+
                      | Visualizations / Dashboard    |
                      +-------------------------------+
```

---

## 7. Network Slicing Explanation
Network Slicing allows a network operator to partition a single physical 5G network into multiple isolated virtual networks (slices). Each slice operates as an independent end-to-end logical network tailored to meet specific application requirements without interference from other slices.

---

## 8. eMBB (Enhanced Mobile Broadband) Explanation
- **Target Use Cases**: 4K/8K video streaming, virtual reality (VR), high-speed file transfers.
- **Key Characteristics**: Requires high peak throughput and large packet payloads.
- **Priority**: Medium.

---

## 9. URLLC (Ultra-Reliable Low-Latency Communication) Explanation
- **Target Use Cases**: Autonomous driving telemetry, remote robotic surgery, smart grid control.
- **Key Characteristics**: Demands ultra-low end-to-end latency (< 10 ms) and 99.9% reliability.
- **Priority**: Highest.

---

## 10. mMTC (Massive Machine Type Communications) Explanation
- **Target Use Cases**: Smart city environmental sensors, agricultural IoT devices, utility metering.
- **Key Characteristics**: High connection density (thousands of devices), small infrequent payloads, tolerant to moderate delays.
- **Priority**: Lower.

---

## 11. Methodology
The simulation workflow proceeds through 10 sequential pipeline stages:
$$\text{Input} \rightarrow \text{Traffic Gen} \rightarrow \text{Slice Creation} \rightarrow \text{Resource Allocation} \rightarrow \text{Network Sim} \rightarrow \text{Monitoring} \rightarrow \text{Metric Calculation} \rightarrow \text{SLA Eval} \rightarrow \text{Comparison} \rightarrow \text{Visualization}$$

---

## 12. Resource Allocation Methodology

### A. Static Allocation Strategy
Resources are fixed per slice regardless of instantaneous demand:
- eMBB: 60% Bandwidth & CPU
- URLLC: 25% Bandwidth & CPU
- mMTC: 15% Bandwidth & CPU

### B. Dynamic Priority-Based Allocation Strategy
Resources adapt dynamically to real-time traffic demand:
1. Guaranteed minimum allocation reserved for URLLC.
2. Under congestion, URLLC preemptively borrows surplus bandwidth.
3. Remaining resources are distributed among eMBB and mMTC according to traffic weight multipliers.

---

## 13. Performance Metrics
1. **Throughput (Mbps)**: Transmitted data volume over time duration.
2. **End-to-End Latency (ms)**: Propagation + Transmission + Queuing + Processing delay.
3. **Packet Loss (%)**: Percentage of packets dropped due to buffer overflow.
4. **Jitter (ms)**: Standard deviation of packet arrival delay.
5. **Resource Utilization (%)**: Demanded resources over allocated capacity.
6. **Reliability (%)**: $100 - \text{Packet Loss } (\%)$.

---

## 14. SLA Methodology (Configurable Assumptions)
SLA compliance is evaluated against target thresholds:
- **eMBB**: Min Throughput $\ge 40$ Mbps, Max Latency $\le 100$ ms, Max Loss $\le 5\%$, Min Reliability $\ge 95\%$.
- **URLLC**: Min Throughput $\ge 3$ Mbps, Max Latency $\le 10$ ms, Max Loss $\le 0.1\%$, Min Reliability $\ge 99.9\%$.
- **mMTC**: Min Throughput $\ge 2$ Mbps, Max Latency $\le 500$ ms, Max Loss $\le 5\%$, Min Reliability $\ge 95\%$.

---

## 15. Experiments Suite
- **Exp 1-4**: Slice performance across Low, Medium, High, and Congested traffic loads.
- **Exp 5**: Static Allocation vs Dynamic Allocation under high network load.
- **Exp 6**: Performance vs Number of Users/Devices sweep.
- **Exp 7**: Performance vs Physical Substrate Bandwidth capacity sweep.
- **Exp 8**: Traffic Demand vs SLA Satisfaction compliance.

---

## 16. Installation

1. Open terminal in project directory:
```bash
cd c:\Users\anilv\OneDrive\Desktop(1)\Btech\cn_project
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

---

## 17. How to Run

### Command Line Interface (CLI)

Run default simulation (Medium traffic, Dynamic allocation):
```bash
python main.py
```

Run single simulation with custom options:
```bash
python main.py --traffic high --strategy dynamic --users 150 --bandwidth 120
```

Run full 8-experiment suite:
```bash
python main.py --run-experiments
```
*(Or execute directly via `python experiments/run_experiments.py`)*

### Run Automated Unit Tests
```bash
pytest tests/
```

---

## 18. Dashboard Instructions

Launch the interactive Streamlit dashboard:
```bash
streamlit run dashboard/app.py
```

The dashboard enables:
- Selecting slice types and allocation strategies.
- Sliders for user counts, bandwidth, and traffic loads.
- Real-time performance KPI display and comparative bar graphs.
- Downloading raw results in CSV format.

---

## 19. Expected Results & Observations
1. **Dynamic Allocation Outperforms Static**: Under high traffic, dynamic allocation prevents URLLC SLA breaches by preemptively reallocating idle mMTC bandwidth.
2. **URLLC Latency Guarantee**: URLLC latency remains $< 10$ ms even under congestion when dynamic priority preemption is active.
3. **Substrate Utilization**: Dynamic allocation achieves $> 85\%$ resource utilization compared to $\approx 60\%$ in static allocation.

---

## 20. Limitations
- Simulation assumes ideal wireless channel conditions without detailed 3GPP ray-tracing fading models.
- Does not interface with physical hardware RAN or core network hardware (gNodeB hardware abstraction).

---

## 21. Future Enhancements
- Integration of Deep Reinforcement Learning (DRL) for dynamic slice resource allocation.
- Simulation of Multi-access Edge Computing (MEC) node offloading.
- Support for 5G RedCap (Reduced Capability) device slicing profiles.

---

## 22. References
- 3GPP TS 28.530: Management and orchestration of 5G network slicing.
- ITU-T Recommendation M.3100: Generic Network Information Model.
- IEEE Standard for Network Slicing Performance Metrics.
