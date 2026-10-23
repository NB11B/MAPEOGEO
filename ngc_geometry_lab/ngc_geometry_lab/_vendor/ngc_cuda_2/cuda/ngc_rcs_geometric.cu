#include "ngc_rcs_api.h"
#include <cuda_runtime.h>
#include <cuComplex.h>
#include <thrust/scan.h>
#include <thrust/device_ptr.h>
#include <thrust/execution_policy.h>
#include <cmath>
#include <chrono>
#include <cstring>
#include <cstdlib>
#include <cstdio>
#include <vector>

#define M_PI 3.14159265358979323846
#define TWO_PI 6.28318530717958647692

/* NGC Candidate State structure */
struct NgcRcsState {
    int n_qubits;
    int ablation_mode;
    size_t num_states;

    /* Dual cores: F+ (primary quantized core) and F- (complementary dual core) */
    cuDoubleComplex* d_state_fplus;
    cuDoubleComplex* d_state_fminus;

    double* d_probs;
    double* d_cdf;

    cudaStream_t stream;
    cudaEvent_t ev_start;
    cudaEvent_t ev_stop;

    /* Quantization tracking */
    int quant_count;
    double sum_quant_error;
    double max_quant_error;

    int phase_bins;
    size_t peak_device_mem;
};

/* PRNG helper: SplitMix64 */
__device__ inline uint64_t ngc_splitmix64(uint64_t x) {
    x += 0x9e3779b97f4a7c15ULL;
    x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9ULL;
    x = (x ^ (x >> 27)) * 0x94d049bb133111ebULL;
    return x ^ (x >> 31);
}

/* Discrete Cyclic Phase Projection Function (Z_N_phi) */
static inline double project_discrete_phase(double theta, int n_bins, double* out_error) {
    if (n_bins <= 0) n_bins = 48;
    /* Normalize theta into [0, 2pi) */
    double norm = std::fmod(theta, TWO_PI);
    if (norm < 0.0) norm += TWO_PI;

    /* k = round(n_bins * (theta mod 2pi) / 2pi) mod n_bins */
    int k = (int)std::round((double)n_bins * (norm / TWO_PI));
    k = ((k % n_bins) + n_bins) % n_bins;

    double theta_q = (TWO_PI * (double)k) / (double)n_bins;

    /* Circular error */
    double diff = std::fabs(norm - theta_q);
    if (diff > M_PI) diff = TWO_PI - diff;

    if (out_error) *out_error = diff;
    return theta_q;
}

/* ========================================================================= */
/* CUDA Kernels for Backend C                                                */
/* ========================================================================= */

__global__ void ngc_init_zero_kernel(cuDoubleComplex* fplus, cuDoubleComplex* fminus, size_t num_states) {
    size_t idx = (size_t)blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < num_states) {
        if (idx == 0) {
            fplus[idx] = make_cuDoubleComplex(1.0, 0.0);
            fminus[idx] = make_cuDoubleComplex(1.0, 0.0);
        } else {
            fplus[idx] = make_cuDoubleComplex(0.0, 0.0);
            fminus[idx] = make_cuDoubleComplex(0.0, 0.0);
        }
    }
}

__global__ void ngc_rz_kernel(cuDoubleComplex* state, size_t num_states, int qubit, double theta) {
    size_t idx = (size_t)blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= num_states) return;

    double half_theta = 0.5 * theta;
    double c = cos(half_theta);
    double s = sin(half_theta);

    int bit = (int)((idx >> qubit) & 1ULL);
    double s_sign = (bit == 0) ? -s : s;

    cuDoubleComplex psi = state[idx];
    double u = cuCreal(psi);
    double v = cuCimag(psi);

    state[idx] = make_cuDoubleComplex(u * c - v * s_sign, v * c + u * s_sign);
}

__global__ void ngc_rx_kernel(cuDoubleComplex* state, size_t num_pairs, int qubit, double theta) {
    size_t k = (size_t)blockIdx.x * blockDim.x + threadIdx.x;
    if (k >= num_pairs) return;

    size_t low_mask = (1ULL << qubit) - 1ULL;
    size_t i0 = (k & low_mask) | ((k >> qubit) << (qubit + 1));
    size_t i1 = i0 | (1ULL << qubit);

    double half_theta = 0.5 * theta;
    double c = cos(half_theta);
    double s = sin(half_theta);

    cuDoubleComplex psi0 = state[i0];
    cuDoubleComplex psi1 = state[i1];

    double u0 = cuCreal(psi0);
    double v0 = cuCimag(psi0);
    double u1 = cuCreal(psi1);
    double v1 = cuCimag(psi1);

    state[i0] = make_cuDoubleComplex(c * u0 + s * v1, c * v0 - s * u1);
    state[i1] = make_cuDoubleComplex(s * v0 + c * u1, -s * u0 + c * v1);
}

__global__ void ngc_cz_kernel(cuDoubleComplex* state, size_t num_states, int qa, int qb) {
    size_t idx = (size_t)blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= num_states) return;

    size_t mask = (1ULL << qa) | (1ULL << qb);
    if ((idx & mask) == mask) {
        cuDoubleComplex psi = state[idx];
        state[idx] = make_cuDoubleComplex(-cuCreal(psi), -cuCimag(psi));
    }
}

__global__ void ngc_ablation_uniform_amp_kernel(cuDoubleComplex* state, size_t num_states) {
    size_t idx = (size_t)blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= num_states) return;

    cuDoubleComplex psi = state[idx];
    double r = cuCreal(psi);
    double i = cuCimag(psi);
    double mag = sqrt(r * r + i * i);
    double inv_norm = 1.0 / sqrt((double)num_states);

    if (mag > 1e-15) {
        state[idx] = make_cuDoubleComplex(r / mag * inv_norm, i / mag * inv_norm);
    } else {
        state[idx] = make_cuDoubleComplex(inv_norm, 0.0);
    }
}

__global__ void ngc_probability_kernel(const cuDoubleComplex* state, double* probs, size_t num_states) {
    size_t idx = (size_t)blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= num_states) return;

    cuDoubleComplex psi = state[idx];
    double r = cuCreal(psi);
    double i = cuCimag(psi);
    probs[idx] = r * r + i * i;
}

__global__ void ngc_sample_kernel(const double* cdf, size_t num_states, double total_mass, uint64_t seed, int num_samples, uint64_t* out_samples) {
    int s = blockIdx.x * blockDim.x + threadIdx.x;
    if (s >= num_samples) return;

    uint64_t h = ngc_splitmix64(seed ^ ((uint64_t)s * 0x9e3779b97f4a7c15ULL));
    double u = (double)(h >> 11) * (1.0 / 9007199254740992.0) * total_mass;

    size_t low = 0;
    size_t high = num_states - 1;
    size_t ans = high;

    while (low <= high) {
        size_t mid = low + ((high - low) >> 1);
        if (cdf[mid] >= u) {
            ans = mid;
            if (mid == 0) break;
            high = mid - 1;
        } else {
            low = mid + 1;
        }
    }

    out_samples[s] = (uint64_t)ans;
}

/* ========================================================================= */
/* C API Implementations for Backend C                                       */
/* ========================================================================= */

NGC_EXPORT int ngc_rcs_create(int n_qubits, int ablation_mode, void** out_handle) {
    if (n_qubits < 1 || n_qubits > 30 || !out_handle) return -1;

    NgcRcsState* s = new NgcRcsState();
    s->n_qubits = n_qubits;
    s->ablation_mode = ablation_mode;
    s->num_states = 1ULL << n_qubits;
    s->phase_bins = 48;
    s->quant_count = 0;
    s->sum_quant_error = 0.0;
    s->max_quant_error = 0.0;

    cudaStreamCreate(&s->stream);
    cudaEventCreate(&s->ev_start);
    cudaEventCreate(&s->ev_stop);

    cudaError_t err1 = cudaMalloc((void**)&s->d_state_fplus, s->num_states * sizeof(cuDoubleComplex));
    cudaError_t err2 = cudaMalloc((void**)&s->d_state_fminus, s->num_states * sizeof(cuDoubleComplex));
    cudaError_t err3 = cudaMalloc((void**)&s->d_probs, s->num_states * sizeof(double));
    cudaError_t err4 = cudaMalloc((void**)&s->d_cdf, s->num_states * sizeof(double));

    if (err1 != cudaSuccess || err2 != cudaSuccess || err3 != cudaSuccess || err4 != cudaSuccess) {
        if (s->d_state_fplus) cudaFree(s->d_state_fplus);
        if (s->d_state_fminus) cudaFree(s->d_state_fminus);
        if (s->d_probs) cudaFree(s->d_probs);
        if (s->d_cdf) cudaFree(s->d_cdf);
        cudaStreamDestroy(s->stream);
        cudaEventDestroy(s->ev_start);
        cudaEventDestroy(s->ev_stop);
        delete s;
        return -2;
    }

    s->peak_device_mem = s->num_states * (2 * sizeof(cuDoubleComplex) + 2 * sizeof(double));

    int block = 256;
    int grid = (int)((s->num_states + block - 1) / block);
    ngc_init_zero_kernel<<<grid, block, 0, s->stream>>>(s->d_state_fplus, s->d_state_fminus, s->num_states);
    cudaStreamSynchronize(s->stream);

    *out_handle = (void*)s;
    return 0;
}

NGC_EXPORT int ngc_rcs_free(void* handle) {
    if (!handle) return -1;
    NgcRcsState* s = (NgcRcsState*)handle;

    if (s->d_state_fplus) cudaFree(s->d_state_fplus);
    if (s->d_state_fminus) cudaFree(s->d_state_fminus);
    if (s->d_probs) cudaFree(s->d_probs);
    if (s->d_cdf) cudaFree(s->d_cdf);

    cudaStreamDestroy(s->stream);
    cudaEventDestroy(s->ev_start);
    cudaEventDestroy(s->ev_stop);

    delete s;
    return 0;
}

NGC_EXPORT int ngc_rcs_reset(void* handle) {
    if (!handle) return -1;
    NgcRcsState* s = (NgcRcsState*)handle;

    s->quant_count = 0;
    s->sum_quant_error = 0.0;
    s->max_quant_error = 0.0;

    int block = 256;
    int grid = (int)((s->num_states + block - 1) / block);
    ngc_init_zero_kernel<<<grid, block, 0, s->stream>>>(s->d_state_fplus, s->d_state_fminus, s->num_states);
    return 0;
}

/* Strict RCS Operator: RZ */
NGC_EXPORT int ngc_rcs_rz(void* handle, int qubit, double theta) {
    if (!handle) return -1;
    NgcRcsState* s = (NgcRcsState*)handle;
    if (qubit < 0 || qubit >= s->n_qubits) return -2;

    double theta_eff = theta;
    if (s->ablation_mode == NGC_ABLATION_NO_PHASE) {
        theta_eff = 0.0;
    } else {
        double err = 0.0;
        theta_eff = project_discrete_phase(theta, s->phase_bins, &err);
        s->quant_count++;
        s->sum_quant_error += err;
        if (err > s->max_quant_error) s->max_quant_error = err;
    }

    int block = 256;
    int grid = (int)((s->num_states + block - 1) / block);

    /* Primary F+ core */
    ngc_rz_kernel<<<grid, block, 0, s->stream>>>(s->d_state_fplus, s->num_states, qubit, theta_eff);

    /* Complementary dual F- core (dual parallax channel) */
    ngc_rz_kernel<<<grid, block, 0, s->stream>>>(s->d_state_fminus, s->num_states, qubit, -theta_eff);

    if (s->ablation_mode == NGC_ABLATION_NO_AMPLITUDE) {
        ngc_ablation_uniform_amp_kernel<<<grid, block, 0, s->stream>>>(s->d_state_fplus, s->num_states);
        ngc_ablation_uniform_amp_kernel<<<grid, block, 0, s->stream>>>(s->d_state_fminus, s->num_states);
    }

    return 0;
}

/* Strict RCS Operator: RX */
NGC_EXPORT int ngc_rcs_rx(void* handle, int qubit, double theta) {
    if (!handle) return -1;
    NgcRcsState* s = (NgcRcsState*)handle;
    if (qubit < 0 || qubit >= s->n_qubits) return -2;

    double theta_eff = theta;
    if (s->ablation_mode == NGC_ABLATION_NO_PHASE) {
        theta_eff = 0.0;
    } else {
        double err = 0.0;
        theta_eff = project_discrete_phase(theta, s->phase_bins, &err);
        s->quant_count++;
        s->sum_quant_error += err;
        if (err > s->max_quant_error) s->max_quant_error = err;
    }

    size_t num_pairs = s->num_states >> 1;
    int block = 256;
    int grid = (int)((num_pairs + block - 1) / block);

    /* Primary F+ core */
    ngc_rx_kernel<<<grid, block, 0, s->stream>>>(s->d_state_fplus, num_pairs, qubit, theta_eff);

    /* Complementary dual F- core */
    ngc_rx_kernel<<<grid, block, 0, s->stream>>>(s->d_state_fminus, num_pairs, qubit, -theta_eff);

    if (s->ablation_mode == NGC_ABLATION_NO_AMPLITUDE) {
        int g_all = (int)((s->num_states + block - 1) / block);
        ngc_ablation_uniform_amp_kernel<<<g_all, block, 0, s->stream>>>(s->d_state_fplus, s->num_states);
        ngc_ablation_uniform_amp_kernel<<<g_all, block, 0, s->stream>>>(s->d_state_fminus, s->num_states);
    }

    return 0;
}

/* Strict RCS Operator: CZ */
NGC_EXPORT int ngc_rcs_cz(void* handle, int q_a, int q_b) {
    if (!handle) return -1;
    NgcRcsState* s = (NgcRcsState*)handle;
    if (q_a < 0 || q_a >= s->n_qubits || q_b < 0 || q_b >= s->n_qubits || q_a == q_b) return -2;

    /* Mode D: Inter-qubit/correlation disabled -> CZ is identity */
    if (s->ablation_mode == NGC_ABLATION_NO_CORRELATION) {
        return 0;
    }

    int block = 256;
    int grid = (int)((s->num_states + block - 1) / block);

    ngc_cz_kernel<<<grid, block, 0, s->stream>>>(s->d_state_fplus, s->num_states, q_a, q_b);
    ngc_cz_kernel<<<grid, block, 0, s->stream>>>(s->d_state_fminus, s->num_states, q_a, q_b);

    return 0;
}

NGC_EXPORT int ngc_rcs_get_probabilities(void* handle, double* out_probs) {
    if (!handle || !out_probs) return -1;
    NgcRcsState* s = (NgcRcsState*)handle;

    int block = 256;
    int grid = (int)((s->num_states + block - 1) / block);
    ngc_probability_kernel<<<grid, block, 0, s->stream>>>(s->d_state_fplus, s->d_probs, s->num_states);

    cudaMemcpyAsync(out_probs, s->d_probs, s->num_states * sizeof(double), cudaMemcpyDeviceToHost, s->stream);
    cudaStreamSynchronize(s->stream);
    return 0;
}

NGC_EXPORT int ngc_rcs_get_statevector(void* handle, double* out_real, double* out_imag) {
    if (!handle || !out_real || !out_imag) return -1;
    NgcRcsState* s = (NgcRcsState*)handle;

    cuDoubleComplex* h_state = (cuDoubleComplex*)malloc(s->num_states * sizeof(cuDoubleComplex));
    if (!h_state) return -2;

    cudaMemcpy(h_state, s->d_state_fplus, s->num_states * sizeof(cuDoubleComplex), cudaMemcpyDeviceToHost);
    for (size_t i = 0; i < s->num_states; ++i) {
        out_real[i] = cuCreal(h_state[i]);
        out_imag[i] = cuCimag(h_state[i]);
    }
    free(h_state);
    return 0;
}

NGC_EXPORT int ngc_rcs_sample(void* handle, uint64_t seed, int num_samples, uint64_t* out_samples) {
    if (!handle || num_samples <= 0 || !out_samples) return -1;
    NgcRcsState* s = (NgcRcsState*)handle;

    int block = 256;
    int grid = (int)((s->num_states + block - 1) / block);
    ngc_probability_kernel<<<grid, block, 0, s->stream>>>(s->d_state_fplus, s->d_probs, s->num_states);

    thrust::device_ptr<double> d_probs_ptr(s->d_probs);
    thrust::device_ptr<double> d_cdf_ptr(s->d_cdf);
    thrust::inclusive_scan(thrust::cuda::par.on(s->stream), d_probs_ptr, d_probs_ptr + s->num_states, d_cdf_ptr);

    double total_mass = 1.0;
    cudaMemcpyAsync(&total_mass, s->d_cdf + (s->num_states - 1), sizeof(double), cudaMemcpyDeviceToHost, s->stream);
    cudaStreamSynchronize(s->stream);

    uint64_t* d_samples = nullptr;
    cudaMalloc((void**)&d_samples, num_samples * sizeof(uint64_t));

    int s_block = 256;
    int s_grid = (num_samples + s_block - 1) / s_block;
    ngc_sample_kernel<<<s_grid, s_block, 0, s->stream>>>(s->d_cdf, s->num_states, total_mass, seed, num_samples, d_samples);

    cudaMemcpyAsync(out_samples, d_samples, num_samples * sizeof(uint64_t), cudaMemcpyDeviceToHost, s->stream);
    cudaStreamSynchronize(s->stream);

    cudaFree(d_samples);
    return 0;
}

/* Parallax metric: ||psi_F+ - psi_F-|| / (||psi_F+|| + ||psi_F-||) */
NGC_EXPORT int ngc_rcs_get_parallax(void* handle, double* out_parallax) {
    if (!handle || !out_parallax) return -1;
    NgcRcsState* s = (NgcRcsState*)handle;

    cuDoubleComplex* h_plus = (cuDoubleComplex*)malloc(s->num_states * sizeof(cuDoubleComplex));
    cuDoubleComplex* h_minus = (cuDoubleComplex*)malloc(s->num_states * sizeof(cuDoubleComplex));
    if (!h_plus || !h_minus) {
        if (h_plus) free(h_plus);
        if (h_minus) free(h_minus);
        return -2;
    }

    cudaMemcpy(h_plus, s->d_state_fplus, s->num_states * sizeof(cuDoubleComplex), cudaMemcpyDeviceToHost);
    cudaMemcpy(h_minus, s->d_state_fminus, s->num_states * sizeof(cuDoubleComplex), cudaMemcpyDeviceToHost);

    double diff_sq = 0.0;
    double norm_plus_sq = 0.0;
    double norm_minus_sq = 0.0;

    for (size_t i = 0; i < s->num_states; ++i) {
        double dr = cuCreal(h_plus[i]) - cuCreal(h_minus[i]);
        double di = cuCimag(h_plus[i]) - cuCimag(h_minus[i]);
        diff_sq += dr * dr + di * di;

        double pr = cuCreal(h_plus[i]);
        double pi = cuCimag(h_plus[i]);
        norm_plus_sq += pr * pr + pi * pi;

        double mr = cuCreal(h_minus[i]);
        double mi = cuCimag(h_minus[i]);
        norm_minus_sq += mr * mr + mi * mi;
    }

    double diff_norm = std::sqrt(diff_sq);
    double denom = std::sqrt(norm_plus_sq) + std::sqrt(norm_minus_sq);
    *out_parallax = (denom > 1e-15) ? (diff_norm / denom) : 0.0;

    free(h_plus);
    free(h_minus);
    return 0;
}

NGC_EXPORT int ngc_rcs_run_circuit(void* handle, const ngc_gate_t* gates, int num_gates, uint64_t seed, int num_samples, uint64_t* out_samples, ngc_perf_stats_t* stats) {
    if (!handle || !gates) return -1;
    NgcRcsState* s = (NgcRcsState*)handle;

    auto t_wall_start = std::chrono::high_resolution_clock::now();

    ngc_rcs_reset(handle);

    int count_rz = 0;
    int count_rx = 0;
    int count_cz = 0;
    int count_meas = 0;

    cudaEventRecord(s->ev_start, s->stream);

    for (int i = 0; i < num_gates; ++i) {
        const ngc_gate_t& g = gates[i];
        if (g.gate_type == GATE_RZ) {
            ngc_rcs_rz(handle, g.qubit_a, g.theta);
            count_rz++;
        } else if (g.gate_type == GATE_RX) {
            ngc_rcs_rx(handle, g.qubit_a, g.theta);
            count_rx++;
        } else if (g.gate_type == GATE_CZ) {
            ngc_rcs_cz(handle, g.qubit_a, g.qubit_b);
            count_cz++;
        } else if (g.gate_type == GATE_MEASURE_ALL) {
            count_meas++;
        }
    }

    cudaEventRecord(s->ev_stop, s->stream);
    cudaEventSynchronize(s->ev_stop);

    float gate_ms = 0.0f;
    cudaEventElapsedTime(&gate_ms, s->ev_start, s->ev_stop);

    float prob_ms = 0.0f;
    float samp_ms = 0.0f;

    if (num_samples > 0 && out_samples) {
        cudaEventRecord(s->ev_start, s->stream);
        int block = 256;
        int grid = (int)((s->num_states + block - 1) / block);
        ngc_probability_kernel<<<grid, block, 0, s->stream>>>(s->d_state_fplus, s->d_probs, s->num_states);
        cudaEventRecord(s->ev_stop, s->stream);
        cudaEventSynchronize(s->ev_stop);
        cudaEventElapsedTime(&prob_ms, s->ev_start, s->ev_stop);

        cudaEventRecord(s->ev_start, s->stream);
        thrust::device_ptr<double> d_probs_ptr(s->d_probs);
        thrust::device_ptr<double> d_cdf_ptr(s->d_cdf);
        thrust::inclusive_scan(thrust::cuda::par.on(s->stream), d_probs_ptr, d_probs_ptr + s->num_states, d_cdf_ptr);

        double total_mass = 1.0;
        cudaMemcpyAsync(&total_mass, s->d_cdf + (s->num_states - 1), sizeof(double), cudaMemcpyDeviceToHost, s->stream);
        cudaStreamSynchronize(s->stream);

        uint64_t* d_samples = nullptr;
        cudaMalloc((void**)&d_samples, num_samples * sizeof(uint64_t));

        int s_block = 256;
        int s_grid = (num_samples + s_block - 1) / s_block;
        ngc_sample_kernel<<<s_grid, s_block, 0, s->stream>>>(s->d_cdf, s->num_states, total_mass, seed, num_samples, d_samples);

        cudaMemcpy(out_samples, d_samples, num_samples * sizeof(uint64_t), cudaMemcpyDeviceToHost);
        cudaFree(d_samples);

        cudaEventRecord(s->ev_stop, s->stream);
        cudaEventSynchronize(s->ev_stop);
        cudaEventElapsedTime(&samp_ms, s->ev_start, s->ev_stop);
    }

    double parallax_val = 0.0;
    ngc_rcs_get_parallax(handle, &parallax_val);

    auto t_wall_end = std::chrono::high_resolution_clock::now();
    double total_ms = std::chrono::duration<double, std::milli>(t_wall_end - t_wall_start).count();

    if (stats) {
        std::memset(stats, 0, sizeof(ngc_perf_stats_t));
        stats->gate_execution_ms = gate_ms;
        stats->probability_ms = prob_ms;
        stats->sampling_ms = samp_ms;
        stats->total_wall_ms = total_ms;
        stats->peak_device_memory_bytes = s->peak_device_mem;
        stats->peak_host_memory_bytes = s->num_states * sizeof(double);
        stats->number_RZ = count_rz;
        stats->number_RX = count_rx;
        stats->number_CZ = count_cz;
        stats->number_measurements = count_meas;
        stats->shots = num_samples;
        if (stats->sampling_ms > 0.0) {
            stats->samples_per_second = (double)num_samples / (stats->sampling_ms * 1e-3);
        }
        if (stats->gate_execution_ms > 0.0) {
            stats->gates_per_second = (double)num_gates / (stats->gate_execution_ms * 1e-3);
        }
        stats->representation_bytes = s->peak_device_mem;
        stats->bytes_per_logical_qubit = s->peak_device_mem / s->n_qubits;
        stats->quantization_operations = s->quant_count;
        stats->max_quantization_error = s->max_quant_error;
        stats->mean_quantization_error = (s->quant_count > 0) ? (s->sum_quant_error / s->quant_count) : 0.0;
        stats->parallax = parallax_val;
    }

    return 0;
}

NGC_EXPORT int ngc_rcs_set_phase_resolution(void* handle, int num_bins) {
    if (!handle || num_bins <= 0) return -1;
    NgcRcsState* s = (NgcRcsState*)handle;
    s->phase_bins = num_bins;
    return 0;
}

NGC_EXPORT int ngc_get_device_info(char* out_name, size_t name_buf_size, size_t* total_mem, size_t* free_mem) {
    int dev = 0;
    cudaError_t err = cudaGetDevice(&dev);
    if (err != cudaSuccess) return -1;

    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, dev);
    if (out_name && name_buf_size > 0) {
        strncpy(out_name, prop.name, name_buf_size - 1);
        out_name[name_buf_size - 1] = '\0';
    }

    if (total_mem && free_mem) {
        cudaMemGetInfo(free_mem, total_mem);
    }
    return 0;
}
