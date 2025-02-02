
Quantum Shor's Algorithm for Integer Factorization

    shors_algorithm.py: The main Python script implementing Shor's algorithm using Qiskit and IBM's quantum services.


Results

After running the algorithm, the script generates the following result, where the most likely phase estimate corresponds to the period rr, which is used to compute potential factors of the number 15.

Here is a plot of the measurement results:

Shor's Algorithm Results
![](shorsalgorithmresults.png)
The factors of 15 found by the algorithm are displayed as:

  gcd(7^(r/2) - 1, 15) = 3
  gcd(7^(r/2) + 1, 15) = 5
