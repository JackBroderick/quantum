import os
import numpy as np
from math import gcd
from fractions import Fraction
from dotenv import load_dotenv
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, Sampler
import matplotlib.pyplot as plt

# Load environment variables from .env file
load_dotenv()

# Retrieve API key from environment variable
api_key = os.getenv("IBM_QUANTUM_API_KEY")
if not api_key:
    raise ValueError("API key not found. Set IBM_QUANTUM_API_KEY in your .env file or environment variables.")

# Authenticate with IBM Quantum service
service = QiskitRuntimeService(channel="ibm_quantum", token=api_key)
print("QiskitRuntimeService loaded and authenticated!")

# Problem Setup
N = 15  # Number to factor
a = 7   # Co-prime integer
N_COUNT = 8  # Number of counting qubits

# Function to create controlled modular exponentiation gate
def c_amod15(a, power):
    if a not in [2, 4, 7, 8, 11, 13]:
        raise ValueError("'a' must be 2, 4, 7, 8, 11, or 13.")
    
    qc = QuantumCircuit(4)
    for _ in range(power):
        if a in [2, 13]:
            qc.swap(2, 3); qc.swap(1, 2); qc.swap(0, 1)
        if a in [7, 8]:
            qc.swap(0, 1); qc.swap(1, 2); qc.swap(2, 3)
        if a in [4, 11]:
            qc.swap(1, 3); qc.swap(0, 2)
        if a in [7, 11, 13]:
            for q in range(4):
                qc.x(q)
    
    gate = qc.to_gate()
    gate.name = f"{a}^{power} mod 15"
    return gate.control(1)

# Function to create inverse Quantum Fourier Transform
def qft_dagger(n):
    qc = QuantumCircuit(n)
    for qubit in range(n // 2):
        qc.swap(qubit, n - qubit - 1)
    for j in range(n):
        for m in range(j):
            qc.cp(-np.pi / 2**(j - m), m, j)
        qc.h(j)
    qc.name = "QFT†"
    return qc

# Create the quantum circuit for Shor's algorithm
qc = QuantumCircuit(N_COUNT + 4, N_COUNT)

# Apply Hadamard to counting qubits
for i in range(N_COUNT):
    qc.h(i)

qc.x(N_COUNT)  # Initialize auxiliary qubit

# Apply modular exponentiation
for i in range(N_COUNT):
    qc.append(c_amod15(a, 2**i), [i] + list(range(N_COUNT, N_COUNT + 4)))

# Apply inverse QFT and measurement
qc.append(qft_dagger(N_COUNT), range(N_COUNT))
qc.measure(range(N_COUNT), range(N_COUNT))
qc.name = "Shor_Example"

# Select backend and transpile circuit
backend = service.least_busy(simulator=False)
print("Using backend:", backend.name)
transpiled_circ = transpile(qc, backend=backend)
sampler = Sampler(mode=backend)
print("Sampler is ready.")

# Run the circuit
job = sampler.run([transpiled_circ], shots=4096)
print(f"Submitted job. Job ID: {job.job_id()}")

# Retrieve and process results
result = job.result()
pub_result = result[0]
counts_dict = pub_result.data.c.get_counts()
shots_used = sum(counts_dict.values())

# Convert measurement results to probabilities
counts_prob = {bitstring: c / shots_used for bitstring, c in counts_dict.items()}

# Print top measurement results
print("\n===== Measurement Results (Top 10) =====")
sorted_counts = sorted(counts_prob.items(), key=lambda x: x[1], reverse=True)[:10]
for (bitstring, prob) in sorted_counts:
    print(f"  {bitstring}: p={prob:.4f}")

# Compute phase estimates
phases = [(int(bitstring, 2) / (2**N_COUNT), prob) for bitstring, prob in counts_prob.items() if prob > 0]
phases.sort(key=lambda x: x[1], reverse=True)

# Extract best phase estimate
best_phase, best_prob = phases[0]
print(f"\nMost likely phase estimate: {best_phase} with p={best_prob:.4f}")

# Convert phase to fraction and find period r
frac = Fraction(best_phase).limit_denominator(N)
r = frac.denominator
s = frac.numerator
print(f"Fraction from phase = {s}/{r}")

# Compute possible factors of N
guess1 = gcd(a**(r//2) - 1, N)
guess2 = gcd(a**(r//2) + 1, N)

# Display results
plt.bar(counts_prob.keys(), counts_prob.values(), color="blue")
plt.xlabel("Measurement Outcomes")
plt.ylabel("Probability")
plt.xticks(rotation=90)
plt.title("Shor's Algorithm Measurement Results")
plt.show()
print("\nPotential factors from guess:")
print(f"  gcd({a}^({r//2}) - 1, {N}) = {guess1}")
print(f"  gcd({a}^({r//2}) + 1, {N}) = {guess2}")
print("\nDone!")
