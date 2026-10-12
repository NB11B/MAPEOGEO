#!/usr/bin/env python3
r"""
TRIAD-APP-0: Frozen Architecture Application Protocol & Verification Harness.
Milestone: TRIAD-APP-0.

Enforces the strict Application Rule of the Frozen Methodological Triad:
    "Application-specific modifications to the three-layer architecture are prohibited.
     Applications may instantiate and test the frozen architecture without adding
     primitives, layers, or relation types."

Every application is modeled as an experimental specimen:
    A_k = (Q, F, X, X_R, I, \mathcal{A}, \pi, \mathcal{V}, \Omega)
where:
    - Q: required functional question
    - F: function to preserve
    - X: available / full state
    - X_R: proposed sufficient representation (X_R \not\Rightarrow X)
    - I: required invariants
    - \mathcal{A}: admissible state/action region
    - \pi: regulatory / control policy
    - \mathcal{V}: viability envelope
    - \Omega: subsystem organization (\Omega(\pi_1, ..., \pi_n))

Evaluates three independent sequential gates:
    Gate L1 (Representation Sufficiency):
        X_R \not\Rightarrow X while Q(X_R) = Q(X)  (or d(Q(X_R), Q(X)) <= \epsilon)
    Gate L2 (Regulatory Sufficiency):
        \pi(X_R) \approx \pi(X)  or  |J(\pi(X_R)) - J(\pi(X))| <= \epsilon_C
    Gate L3 (Organizational Sufficiency):
        \Omega(\pi_1, ..., \pi_n) -> F \in \mathcal{V}

Provides exact Diagnostic Failure Localization:
    - L1_FAILURE: Q(X_R) != Q(X)
    - L2_FAILURE: Q(X_R) == Q(X) but \pi(X_R) != \pi(X)
    - L3_FAILURE: Individual controllers succeed, but interaction violates \mathcal{V}
    - TRIAD_CONGRUENT: All three gates pass
"""

from __future__ import annotations

import enum
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


class GateStatus(str, enum.Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_REACHED = "NOT_REACHED"


class DiagnosticVerdict(str, enum.Enum):
    TRIAD_CONGRUENT = "TRIAD_CONGRUENT"
    L1_FAILURE = "L1_FAILURE"
    L2_FAILURE = "L2_FAILURE"
    L3_FAILURE = "L3_FAILURE"


@dataclass
class Layer1Spec:
    full_state_X: str
    question_Q: str
    reduced_state_XR: str
    invariants_I: List[str]
    omitted_information: str
    lossless_reconstruction_possible: bool
    q_error: float
    q_tolerance: float


@dataclass
class Layer2Spec:
    controlled_variables: List[str]
    observed_variables: List[str]
    policy_pi: str
    feedback_stages: List[str]
    control_cost_delta: float
    control_cost_tolerance: float


@dataclass
class Layer3Spec:
    subsystems: List[str]
    local_functions: Dict[str, str]
    coordination_mechanism: str
    viability_envelope_V: Dict[str, Tuple[float, float]]  # variable -> (min_val, max_val)
    observed_envelope_values: Dict[str, float]


@dataclass
class FailureBoundariesSpec:
    l1_failure_conditions: str
    l2_failure_conditions: str
    l3_failure_conditions: str


@dataclass
class ApplicationSpecimen:
    application_id: str
    name: str
    functional_requirement_F: str
    layer_1: Layer1Spec
    layer_2: Layer2Spec
    layer_3: Layer3Spec
    failure_boundaries: FailureBoundariesSpec


@dataclass
class GateEvaluationResult:
    gate_l1_status: GateStatus
    gate_l1_detail: str
    gate_l2_status: GateStatus
    gate_l2_detail: str
    gate_l3_status: GateStatus
    gate_l3_detail: str
    diagnostic_verdict: DiagnosticVerdict
    diagnostic_explanation: str


class TriadApplicationHarness:
    """
    Standardized execution and diagnostic engine for testing applications
    through the frozen 3-layer triad without architectural drift.
    """

    def __init__(self) -> None:
        self.specimens: Dict[str, ApplicationSpecimen] = {}
        self._init_reference_specimens()

    def register_specimen(self, specimen: ApplicationSpecimen) -> None:
        self.specimens[specimen.application_id] = specimen

    def evaluate_specimen(self, specimen: ApplicationSpecimen) -> GateEvaluationResult:
        """
        Executes the three sequential independent gates:
        L1 (Representation) -> L2 (Regulation) -> L3 (Organization).
        """
        # -------------------------------------------------------------
        # Gate L1: Representation Sufficiency
        # Condition: X_R \not\Rightarrow X and d(Q(X_R), Q(X)) <= eps
        # -------------------------------------------------------------
        l1 = specimen.layer_1
        l1_sufficient = (l1.q_error <= l1.q_tolerance)
        if not l1_sufficient:
            return GateEvaluationResult(
                gate_l1_status=GateStatus.FAILED,
                gate_l1_detail=f"Q(X_R) diverged: error {l1.q_error:.4f} > tolerance {l1.q_tolerance:.4f}",
                gate_l2_status=GateStatus.NOT_REACHED,
                gate_l2_detail="Gate L2 not evaluated due to L1 failure.",
                gate_l3_status=GateStatus.NOT_REACHED,
                gate_l3_detail="Gate L3 not evaluated due to L1 failure.",
                diagnostic_verdict=DiagnosticVerdict.L1_FAILURE,
                diagnostic_explanation="Representation is insufficient: the reduced state discarded question-critical structure.",
            )

        gate_l1_detail = (
            f"Passed (error {l1.q_error:.4f} <= tol {l1.q_tolerance:.4f}; "
            f"Lossless reconstruction={l1.lossless_reconstruction_possible})"
        )

        # -------------------------------------------------------------
        # Gate L2: Regulatory Sufficiency
        # Condition: J(\pi(X_R)) - J(\pi(X)) <= eps_C
        # -------------------------------------------------------------
        l2 = specimen.layer_2
        l2_sufficient = (l2.control_cost_delta <= l2.control_cost_tolerance)
        if not l2_sufficient:
            return GateEvaluationResult(
                gate_l1_status=GateStatus.PASSED,
                gate_l1_detail=gate_l1_detail,
                gate_l2_status=GateStatus.FAILED,
                gate_l2_detail=f"Control policy diverged: cost delta {l2.control_cost_delta:.4f} > tol {l2.control_cost_tolerance:.4f}",
                gate_l3_status=GateStatus.NOT_REACHED,
                gate_l3_detail="Gate L3 not evaluated due to L2 failure.",
                diagnostic_verdict=DiagnosticVerdict.L2_FAILURE,
                diagnostic_explanation="Regulatory insufficiency: mathematical reduction preserved Q, but omitted information was critical to control policy pi.",
            )

        gate_l2_detail = f"Passed (cost delta {l2.control_cost_delta:.4f} <= tol {l2.control_cost_tolerance:.4f})"

        # -------------------------------------------------------------
        # Gate L3: Organizational Sufficiency
        # Condition: \Omega(\pi_1, ..., \pi_n) -> F \in \mathcal{V}
        # -------------------------------------------------------------
        l3 = specimen.layer_3
        viability_violations = []
        for var_name, (min_v, max_v) in l3.viability_envelope_V.items():
            obs = l3.observed_envelope_values.get(var_name)
            if obs is None:
                viability_violations.append(f"{var_name}: unobserved")
            elif not (min_v <= obs <= max_v):
                viability_violations.append(f"{var_name}: {obs:.2f} outside [{min_v:.2f}, {max_v:.2f}]")

        if viability_violations:
            return GateEvaluationResult(
                gate_l1_status=GateStatus.PASSED,
                gate_l1_detail=gate_l1_detail,
                gate_l2_status=GateStatus.PASSED,
                gate_l2_detail=gate_l2_detail,
                gate_l3_status=GateStatus.FAILED,
                gate_l3_detail=f"Viability envelope breached: {', '.join(viability_violations)}",
                diagnostic_verdict=DiagnosticVerdict.L3_FAILURE,
                diagnostic_explanation="Organizational failure: individual regulators functioned, but their coupled subsystem interaction destabilized the collective function F.",
            )

        gate_l3_detail = f"Passed (all {len(l3.viability_envelope_V)} viability variables strictly within bounds)"

        return GateEvaluationResult(
            gate_l1_status=GateStatus.PASSED,
            gate_l1_detail=gate_l1_detail,
            gate_l2_status=GateStatus.PASSED,
            gate_l2_detail=gate_l2_detail,
            gate_l3_status=GateStatus.PASSED,
            gate_l3_detail=gate_l3_detail,
            diagnostic_verdict=DiagnosticVerdict.TRIAD_CONGRUENT,
            diagnostic_explanation="Full Triad Congruence: The application specimen is completely realized across Representation, Regulation, and Organization.",
        )

    def generate_standard_report(self, specimen_id: str) -> str:
        """
        Generates the exact standardized report block required by TRIAD-APP-0.
        """
        spec = self.specimens.get(specimen_id)
        if not spec:
            raise KeyError(f"Specimen {specimen_id} not registered.")

        eval_res = self.evaluate_specimen(spec)

        lines = [
            f"APPLICATION: {spec.application_id} - {spec.name}",
            f"FUNCTIONAL_REQUIREMENT: {spec.functional_requirement_F}",
            "",
            "LAYER_1",
            f"full_state: {spec.layer_1.full_state_X}",
            f"question: {spec.layer_1.question_Q}",
            f"reduced_state: {spec.layer_1.reduced_state_XR}",
            f"invariants: {', '.join(spec.layer_1.invariants_I)}",
            f"omitted_information: {spec.layer_1.omitted_information}",
            f"sufficiency_result: {eval_res.gate_l1_status.value} ({eval_res.gate_l1_detail})",
            "",
            "LAYER_2",
            f"controlled_variables: {', '.join(spec.layer_2.controlled_variables)}",
            f"observed_variables: {', '.join(spec.layer_2.observed_variables)}",
            f"policy: {spec.layer_2.policy_pi}",
            f"feedback: {' -> '.join(spec.layer_2.feedback_stages)}",
            f"control_equivalence_result: {eval_res.gate_l2_status.value} ({eval_res.gate_l2_detail})",
            "",
            "LAYER_3",
            f"subsystems: {', '.join(spec.layer_3.subsystems)}",
            f"local_functions: {'; '.join(f'{k}: {v}' for k, v in spec.layer_3.local_functions.items())}",
            f"coordination: {spec.layer_3.coordination_mechanism}",
            f"viability_envelope: {'; '.join(f'{k} in [{v[0]}, {v[1]}]' for k, v in spec.layer_3.viability_envelope_V.items())}",
            f"organizational_result: {eval_res.gate_l3_status.value} ({eval_res.gate_l3_detail})",
            "",
            "FAILURE_BOUNDARIES",
            f"L1_failure_conditions: {spec.failure_boundaries.l1_failure_conditions}",
            f"L2_failure_conditions: {spec.failure_boundaries.l2_failure_conditions}",
            f"L3_failure_conditions: {spec.failure_boundaries.l3_failure_conditions}",
            "",
            f"OVERALL_VERDICT: {eval_res.diagnostic_verdict.value}",
            f"DIAGNOSTIC_EXPLANATION: {eval_res.diagnostic_explanation}",
        ]
        return "\n".join(lines)

    def _init_reference_specimens(self) -> None:
        """
        Initializes reference application specimens:
        1. Reference / Simulated Application Specimen: Resilient Data Center Compute Service
        2. Reference / Simulated Application Specimen: Autonomous Microgrid Frequency Regulation
        3. Reference / Simulated Application Specimen: Coordinated Search-and-Rescue Drone Swarm
        4. Controlled Probe: L1 Failure (Over-Aggressive Dimension Loss)
        5. Controlled Probe: L2 Failure (Omitted Variance Diverges Control Gain)
        6. Controlled Probe: L3 Failure (Subsystem Interaction Destabilization)
        """
        # Specimen 1: Resilient Data Center Compute Service (The User's Exemplar)
        s1 = ApplicationSpecimen(
            application_id="APP_01_DATACENTER",
            name="Autonomous Resilient Data Center Compute Service",
            functional_requirement_F="Continuous high-throughput compute service preserved despite thermal, power, and workload shocks.",
            layer_1=Layer1Spec(
                full_state_X="10^5 time-series streams: per-core temperatures, fan RPMs, branch voltage/currents, thread queues, memory buses.",
                question_Q="Q(X): Does sufficient headroom exist across thermal, power, and queue dimensions to sustain service?",
                reduced_state_XR="X_R = (thermal_margin, power_margin, queue_pressure, redundancy_margin) in R^4.",
                invariants_I=["Conservation of energy balance", "Total job conservation (routed + queued = incoming)"],
                omitted_information="Individual CPU core thermal micro-oscillations, server-level fan harmonic speeds, thread scheduling jitter.",
                lossless_reconstruction_possible=False,
                q_error=0.002,
                q_tolerance=0.05,
            ),
            layer_2=Layer2Spec(
                controlled_variables=["Workload routing ratio", "CRAC cooling setpoint", "Core clock throttling factor", "Job migration count"],
                observed_variables=["Thermal margin Delta T", "Power margin Delta P", "Queue arrival rate lambda", "Active node count N_active"],
                policy_pi="Multi-tiered priority controller: route load when queue_pressure high; throttle when thermal_margin near zero; shed non-critical jobs at boundary.",
                feedback_stages=["OBSERVE_MARGINS", "COMPARE_SAFETY_SETPOINTS", "SELECT_DISSIPATIVE_DRIVE", "ACT_CHASSIS_THROTTLE", "FEEDBACK_TEMPERATURE_DECAY"],
                control_cost_delta=0.014,
                control_cost_tolerance=0.05,
            ),
            layer_3=Layer3Spec(
                subsystems=["Chassis Cooling Regulators", "Cluster Job Load Balancer", "Power Distribution Units"],
                local_functions={
                    "Cooling": "Local variable-speed fan PID regulation",
                    "Load Balancer": "Workload dispatch based on queue pressure",
                    "PDU": "Peak-shaving battery reserve injection",
                },
                coordination_mechanism="Selective margin broadcasting: local regulators act independently; global migration triggers only on shared pressure warning.",
                viability_envelope_V={
                    "max_server_temp_C": (15.0, 85.0),
                    "total_facility_power_MW": (0.1, 10.0),
                    "p99_latency_ms": (1.0, 50.0),
                    "redundancy_ratio": (1.2, 3.0),
                },
                observed_envelope_values={
                    "max_server_temp_C": 74.2,
                    "total_facility_power_MW": 8.4,
                    "p99_latency_ms": 18.5,
                    "redundancy_ratio": 1.45,
                },
            ),
            failure_boundaries=FailureBoundariesSpec(
                l1_failure_conditions="Disregarding localized hotspots by averaging temperatures across entire server rows.",
                l2_failure_conditions="Cooling actuators react too slowly to sudden power spikes due to missing rate-of-change telemetry.",
                l3_failure_conditions="Load balancer routes traffic away from hot servers into cool servers, causing runaway cascading thermal trip in the target zone.",
            ),
        )
        self.register_specimen(s1)

        # Specimen 2: Autonomous Microgrid Frequency Regulation
        s2 = ApplicationSpecimen(
            application_id="APP_02_MICROGRID",
            name="Autonomous Islanded Microgrid Frequency Stabilizer",
            functional_requirement_F="Maintain microgrid frequency and voltage within operational bounds under 60% intermittent renewable penetration.",
            layer_1=Layer1Spec(
                full_state_X="Bus voltage/current waveforms (4 kHz sampling), inverter PWM switching angles, individual solar irradiance sensors.",
                question_Q="Q(X): Is grid active/reactive power generation balanced with instantaneous load?",
                reduced_state_XR="X_R = (frequency_deviation_df, voltage_deviation_dV, rocof_df_dt) in R^3.",
                invariants_I=["Swing equation dynamic invariant", "Reactive power voltage drop relation"],
                omitted_information="Instantaneous sub-cycle inverter harmonics, solar panel MPPT voltage dither.",
                lossless_reconstruction_possible=False,
                q_error=0.001,
                q_tolerance=0.01,
            ),
            layer_2=Layer2Spec(
                controlled_variables=["Inverter synthetic inertia torque", "Battery droop power P_b", "Capacitor bank VAR injection Q_c"],
                observed_variables=["Local grid frequency f", "Local RMS voltage V_rms"],
                policy_pi="Droop control: Delta P = -K_f * Delta f; Delta Q = -K_v * Delta V with virtual inertia emulation.",
                feedback_stages=["SAMPLE_PHASOR", "EXTRACT_FREQUENCY", "COMPARE_NOMINAL_60HZ", "ACT_INVERTER_CURRENT", "FEEDBACK_GRID_FREQUENCY"],
                control_cost_delta=0.005,
                control_cost_tolerance=0.02,
            ),
            layer_3=Layer3Spec(
                subsystems=["Grid-Forming Battery Inverters", "Solar Curtailment Regulators", "Diesel Emergency Generator"],
                local_functions={
                    "Battery": "Instantaneous virtual inertia injection",
                    "Solar": "Fast active power curtailment during over-frequency",
                    "Diesel": "Slow secondary base-load recovery",
                },
                coordination_mechanism="Frequency bus signaling: grid frequency itself acts as the communication-free coordination signal across all devices.",
                viability_envelope_V={
                    "frequency_Hz": (59.5, 60.5),
                    "voltage_pu": (0.95, 1.05),
                    "battery_soc": (0.20, 0.95),
                },
                observed_envelope_values={
                    "frequency_Hz": 59.92,
                    "voltage_pu": 0.985,
                    "battery_soc": 0.62,
                },
            ),
            failure_boundaries=FailureBoundariesSpec(
                l1_failure_conditions="Omitting rate-of-change-of-frequency (RoCoF), preventing timely synthetic inertia response.",
                l2_failure_conditions="Droop gain set too high, exciting inverter PWM LC filter resonance.",
                l3_failure_conditions="Battery and diesel controllers simultaneously ramp down power, triggering secondary frequency collapse.",
            ),
        )
        self.register_specimen(s2)

        # Specimen 3: Coordinated Search-and-Rescue Drone Swarm
        s3 = ApplicationSpecimen(
            application_id="APP_03_DRONE_SWARM",
            name="Decentralized Search-and-Rescue Swarm Locomotion",
            functional_requirement_F="Sustain 95% spatial coverage of disaster zone without mid-air collision despite GPS/comms jamming.",
            layer_1=Layer1Spec(
                full_state_X="Global 6-DOF poses of 30 drones, raw LiDAR point clouds, motor RPM telemetry.",
                question_Q="Q(X): What heading velocity vector maximizes search coverage while maintaining collision-free separation?",
                reduced_state_XR="X_R = (local_voronoi_centroid, min_obstacle_bearing, neighbor_relative_distance) in R^5.",
                invariants_I=["Voronoi partition topological conservation", "Kinematic speed limits"],
                omitted_information="Global absolute GPS coordinates, other drones' battery levels and internal camera image feeds.",
                lossless_reconstruction_possible=False,
                q_error=0.008,
                q_tolerance=0.03,
            ),
            layer_2=Layer2Spec(
                controlled_variables=["Body pitch/roll tilt commands", "Yaw rate", "Rotor thrust"],
                observed_variables=["Relative neighbor distance d_rel", "Local centroid vector c_voronoi"],
                policy_pi="Potential field controller: attractive drive toward Voronoi centroid, repulsive barrier force from neighbors within radius r_safe.",
                feedback_stages=["SENSE_OPTICAL_FLOW", "PROJECT_VORONOI_CENTROID", "COMPUTE_REPULSIVE_FORCE", "ACT_ROTOR_ACCELERATION", "FEEDBACK_RELATIVE_MOTION"],
                control_cost_delta=0.012,
                control_cost_tolerance=0.04,
            ),
            layer_3=Layer3Spec(
                subsystems=["Navigation Regulators", "Obstacle Avoidance Modules", "Triage Beacon Transponders"],
                local_functions={
                    "Nav": "Drive drone toward unsearched Voronoi area",
                    "Avoidance": "Override heading if obstacle distance < 2.0m",
                    "Beacon": "Emit acoustic ping when survivor detected",
                },
                coordination_mechanism="Emergent spatial self-organization via local kinematic collision repulsion without centralized leader.",
                viability_envelope_V={
                    "min_inter_drone_distance_m": (1.5, 500.0),
                    "coverage_percentage": (90.0, 100.0),
                    "battery_flight_time_min": (5.0, 45.0),
                },
                observed_envelope_values={
                    "min_inter_drone_distance_m": 3.8,
                    "coverage_percentage": 96.4,
                    "battery_flight_time_min": 24.0,
                },
            ),
            failure_boundaries=FailureBoundariesSpec(
                l1_failure_conditions="Disregarding relative velocity of approaching neighbors, considering only static distance.",
                l2_failure_conditions="Repulsive potential field gain insufficient to overcome maximum drone momentum during high-speed wind gusts.",
                l3_failure_conditions="Swarm gets trapped in local minimum of concave obstacle boundary, abandoning search coverage.",
            ),
        )
        self.register_specimen(s3)

        # Specimen 4: Controlled Diagnostic Probe - L1 Failure
        s4 = ApplicationSpecimen(
            application_id="PROBE_01_L1_FAIL",
            name="Averaged Acoustic Scene Classifier (L1 Failure Probe)",
            functional_requirement_F="Detect approaching acoustic projectile signature from 64-channel microphone array.",
            layer_1=Layer1Spec(
                full_state_X="64-channel 48kHz audio PCM streams (spatial acoustic field).",
                question_Q="Q(X): What is the azimuth arrival angle and Doppler signature of the target?",
                reduced_state_XR="X_R = total_sound_pressure_level in R^1 (Scalarized SPL).",
                invariants_I=["Acoustic energy conservation"],
                omitted_information="Phase delays between microphone elements, frequency Doppler shifts.",
                lossless_reconstruction_possible=False,
                q_error=0.88,  # Massive divergence!
                q_tolerance=0.05,
            ),
            layer_2=Layer2Spec(
                controlled_variables=["Turret aiming angle"],
                observed_variables=["Total sound pressure level"],
                policy_pi="Aim turret toward sound pressure gradient.",
                feedback_stages=["MEASURE_SPL", "SELECT_AIM", "DRIVE_SERVO", "FEEDBACK_POSITION"],
                control_cost_delta=0.0,
                control_cost_tolerance=0.05,
            ),
            layer_3=Layer3Spec(
                subsystems=["Acoustic Array", "Turret Actuator"],
                local_functions={"Acoustic": "Sum SPL", "Turret": "Rotate"},
                coordination_mechanism="Direct coupling",
                viability_envelope_V={"tracking_error_deg": (0.0, 5.0)},
                observed_envelope_values={"tracking_error_deg": 45.0},
            ),
            failure_boundaries=FailureBoundariesSpec(
                l1_failure_conditions="Scalarizing multi-channel phase delays into total sound level destroys directional information.",
                l2_failure_conditions="N/A",
                l3_failure_conditions="N/A",
            ),
        )
        self.register_specimen(s4)

        # Specimen 5: Controlled Diagnostic Probe - L2 Failure
        s5 = ApplicationSpecimen(
            application_id="PROBE_02_L2_FAIL",
            name="Mean-Only Active Suspension Damping (L2 Failure Probe)",
            functional_requirement_F="Isolate vehicle chassis vibration under severe off-road terrain shock.",
            layer_1=Layer1Spec(
                full_state_X="Chassis displacement, velocity, road elevation profile, damper fluid pressure.",
                question_Q="Q(X): What is the mean road elevation trend over the next 10 meters?",
                reduced_state_XR="X_R = mean_road_slope in R^1.",
                invariants_I=["Chassis kinetic energy balance"],
                omitted_information="High-frequency road elevation variance and cobblestone shock impulses.",
                lossless_reconstruction_possible=False,
                q_error=0.02,  # L1 passes!
                q_tolerance=0.05,
            ),
            layer_2=Layer2Spec(
                controlled_variables=["Damper valve hydraulic orifice area"],
                observed_variables=["Mean road slope"],
                policy_pi="Set damper stiffness strictly proportional to mean road slope.",
                feedback_stages=["OBSERVE_SLOPE", "SELECT_DAMPING", "ACT_VALVE", "FEEDBACK_MOTION"],
                control_cost_delta=0.38,  # L2 fails! Cost exceeds tolerance due to lack of variance knowledge
                control_cost_tolerance=0.05,
            ),
            layer_3=Layer3Spec(
                subsystems=["Front Dampers", "Rear Dampers", "Chassis Leveler"],
                local_functions={"Front": "Damp", "Rear": "Damp", "Leveler": "Level"},
                coordination_mechanism="Shared chassis pitch link",
                viability_envelope_V={"chassis_acceleration_g": (0.0, 1.2)},
                observed_envelope_values={"chassis_acceleration_g": 3.1},
            ),
            failure_boundaries=FailureBoundariesSpec(
                l1_failure_conditions="N/A",
                l2_failure_conditions="Omitting road variance prevents optimal skyhook damping gain, causing harsh bottom-out shock.",
                l3_failure_conditions="N/A",
            ),
        )
        self.register_specimen(s5)

        # Specimen 6: Controlled Diagnostic Probe - L3 Failure
        s6 = ApplicationSpecimen(
            application_id="PROBE_03_L3_FAIL",
            name="Uncoordinated Dual-Pump Cooling Loop (L3 Failure Probe)",
            functional_requirement_F="Maintain nuclear reactor cooling jacket temperature below 90C.",
            layer_1=Layer1Spec(
                full_state_X="Fluid temperature, pressure, and flow velocity across 200 piping nodes.",
                question_Q="Q(X): Does local pump discharge pressure meet jacket delivery specifications?",
                reduced_state_XR="X_R = (local_pressure_p, local_temperature_T) in R^2.",
                invariants_I=["Navier-Stokes mass conservation"],
                omitted_information="Turbulent eddy distributions, micro-bubble cavitation bubbles.",
                lossless_reconstruction_possible=False,
                q_error=0.01,  # L1 passes
                q_tolerance=0.05,
            ),
            layer_2=Layer2Spec(
                controlled_variables=["Pump motor impeller RPM"],
                observed_variables=["Local inlet pressure"],
                policy_pi="Fast proportional regulator: ramp RPM aggressively whenever local pressure drops.",
                feedback_stages=["SENSE_P", "COMPUTE_RPM", "ACT_MOTOR", "FEEDBACK_P"],
                control_cost_delta=0.02,  # L2 passes
                control_cost_tolerance=0.05,
            ),
            layer_3=Layer3Spec(
                subsystems=["Primary Circulation Pump A", "Secondary Circulation Pump B"],
                local_functions={
                    "Pump A": "Regulate circuit A pressure",
                    "Pump B": "Regulate circuit B pressure",
                },
                coordination_mechanism="Uncoupled parallel loop feeding shared mixing manifold (Zero cross-coordination).",
                viability_envelope_V={
                    "jacket_temperature_C": (40.0, 90.0),
                    "manifold_pressure_bar": (2.0, 15.0),
                },
                observed_envelope_values={
                    "jacket_temperature_C": 114.5,  # Breached!
                    "manifold_pressure_bar": 21.3,  # Breached!
                },
            ),
            failure_boundaries=FailureBoundariesSpec(
                l1_failure_conditions="N/A",
                l2_failure_conditions="N/A",
                l3_failure_conditions="Hydraulic water-hammer resonance: Pump A and Pump B enter counter-phase oscillation, creating cavitation and thermal trip.",
            ),
        )
        self.register_specimen(s6)


def main() -> None:
    harness = TriadApplicationHarness()
    print("=" * 80)
    print("TRIAD-APP-0: FROZEN ARCHITECTURE APPLICATION PROTOCOL")
    print("=" * 80)

    for app_id in harness.specimens:
        print("\n" + "=" * 80)
        report = harness.generate_standard_report(app_id)
        print(report)
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
