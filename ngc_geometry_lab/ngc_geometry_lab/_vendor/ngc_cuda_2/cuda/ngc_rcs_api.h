#ifndef NGC_RCS_API_H
#define NGC_RCS_API_H

#include <stdint.h>
#include <stddef.h>

#ifdef _WIN32
  #define NGC_EXPORT __declspec(dllexport)
#else
  #define NGC_EXPORT __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

/* Ablation modes for Backend C (NGC candidate) */
typedef enum {
    NGC_ABLATION_NONE = 0,         /* Mode A: Full NGC candidate with GF(48) */
    NGC_ABLATION_NO_PHASE = 1,      /* Mode B: Phase mechanism disabled */
    NGC_ABLATION_NO_AMPLITUDE = 2,  /* Mode C: Amplitude mechanism disabled */
    NGC_ABLATION_NO_CORRELATION = 3 /* Mode D: Inter-qubit/correlation disabled */
} ngc_ablation_mode_t;

/* Gate types */
typedef enum {
    GATE_RZ = 0,
    GATE_RX = 1,
    GATE_CZ = 2,
    GATE_MEASURE_ALL = 3
} ngc_gate_type_t;

/* Single gate descriptor */
typedef struct {
    int gate_type;
    int qubit_a;
    int qubit_b;
    double theta;
} ngc_gate_t;

/* Execution and profiling statistics */
typedef struct {
    double circuit_parse_ms;
    double initialization_ms;
    double h2d_ms;
    double gate_execution_ms;
    double probability_ms;
    double sampling_ms;
    double d2h_ms;
    double total_wall_ms;
    size_t peak_host_memory_bytes;
    size_t peak_device_memory_bytes;
    int number_RZ;
    int number_RX;
    int number_CZ;
    int number_measurements;
    int shots;
    double samples_per_second;
    double gates_per_second;
    /* NGC-specific */
    size_t representation_bytes;
    size_t bytes_per_logical_qubit;
    int quantization_operations;
    int reconstruction_operations;
    double reconstruction_ms;
    double max_quantization_error;
    double mean_quantization_error;
    double parallax;
} ngc_perf_stats_t;

/* ========================================================================= */
/* Backend B: Conventional CUDA Control Statevector API                      */
/* ========================================================================= */

NGC_EXPORT int cuda_sv_create(int n_qubits, void** out_handle);
NGC_EXPORT int cuda_sv_free(void* handle);
NGC_EXPORT int cuda_sv_reset(void* handle);
NGC_EXPORT int cuda_sv_rz(void* handle, int qubit, double theta);
NGC_EXPORT int cuda_sv_rx(void* handle, int qubit, double theta);
NGC_EXPORT int cuda_sv_cz(void* handle, int q_a, int q_b);
NGC_EXPORT int cuda_sv_get_probabilities(void* handle, double* out_probs);
NGC_EXPORT int cuda_sv_get_statevector(void* handle, double* out_real, double* out_imag);
NGC_EXPORT int cuda_sv_sample(void* handle, uint64_t seed, int num_samples, uint64_t* out_samples);
NGC_EXPORT int cuda_sv_run_circuit(void* handle, const ngc_gate_t* gates, int num_gates, uint64_t seed, int num_samples, uint64_t* out_samples, ngc_perf_stats_t* stats);

/* ========================================================================= */
/* Backend C: NGC Candidate API (Strictly No Target Guidance)                */
/* ========================================================================= */

NGC_EXPORT int ngc_rcs_create(int n_qubits, int ablation_mode, void** out_handle);
NGC_EXPORT int ngc_rcs_free(void* handle);
NGC_EXPORT int ngc_rcs_reset(void* handle);
NGC_EXPORT int ngc_rcs_rz(void* handle, int qubit, double theta);
NGC_EXPORT int ngc_rcs_rx(void* handle, int qubit, double theta);
NGC_EXPORT int ngc_rcs_cz(void* handle, int q_a, int q_b);
NGC_EXPORT int ngc_rcs_get_probabilities(void* handle, double* out_probs);
NGC_EXPORT int ngc_rcs_get_statevector(void* handle, double* out_real, double* out_imag);
NGC_EXPORT int ngc_rcs_sample(void* handle, uint64_t seed, int num_samples, uint64_t* out_samples);
NGC_EXPORT int ngc_rcs_run_circuit(void* handle, const ngc_gate_t* gates, int num_gates, uint64_t seed, int num_samples, uint64_t* out_samples, ngc_perf_stats_t* stats);
NGC_EXPORT int ngc_rcs_get_parallax(void* handle, double* out_parallax);
NGC_EXPORT int ngc_rcs_set_phase_resolution(void* handle, int num_bins);

/* Hardware diagnostic & memory info */
NGC_EXPORT int ngc_get_device_info(char* out_name, size_t name_buf_size, size_t* total_mem, size_t* free_mem);

#ifdef __cplusplus
}
#endif

#endif /* NGC_RCS_API_H */
