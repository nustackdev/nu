import math
import random
import time
from typing import Any, List, Tuple


class HeavyMathProcessor:
    """
    A class containing computationally intensive mathematical operations
    suitable for testing distributed computing systems.
    """

    @classmethod
    def prime_factorization(cls, n: int) -> List[int]:
        """
        Compute prime factorization using trial division.
        Very CPU-intensive for large numbers.
        """
        factors = []
        d = 2

        while d * d <= n:
            while n % d == 0:
                factors.append(d)
                n //= d
            d += 1

        if n > 1:
            factors.append(n)

        return factors

    @classmethod
    def monte_carlo_pi(cls, iterations: int) -> float:
        """
        Estimate pi using Monte Carlo method.
        CPU-intensive due to random number generation and iteration count.
        """
        inside_circle = 0

        for _ in range(iterations):
            x = random.uniform(-1, 1)
            y = random.uniform(-1, 1)

            if x * x + y * y <= 1:
                inside_circle += 1

        return 4 * inside_circle / iterations

    @classmethod
    def is_prime_trial_division(cls, n: int) -> bool:
        """
        Check if a number is prime using trial division.
        Intensive for large numbers.
        """
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False

        # Check odd divisors up to sqrt(n)
        for i in range(3, int(math.sqrt(n)) + 1, 2):
            if n % i == 0:
                return False

        return True

    @classmethod
    def numerical_integration(cls, func_type: str, a: float, b: float, n: int) -> float:
        """
        Numerical integration using trapezoidal rule.
        Intensive due to function evaluations.

        func_type options: 'sin', 'cos', 'exp', 'log', 'polynomial'
        """
        h = (b - a) / n
        result = 0

        def evaluate_function(x: float) -> float:
            if func_type == "sin":
                return math.sin(x)
            elif func_type == "cos":
                return math.cos(x)
            elif func_type == "exp":
                return math.exp(x) if x < 700 else math.exp(700)  # Prevent overflow
            elif func_type == "log":
                return math.log(x) if x > 0 else 0
            elif func_type == "polynomial":
                return x**3 - 2 * x**2 + 3 * x - 1
            else:
                return x**2

        # Trapezoidal rule
        result = evaluate_function(a) + evaluate_function(b)
        for i in range(1, n):
            x = a + i * h
            result += 2 * evaluate_function(x)

        return result * h / 2

    @classmethod
    def benchmark_method(cls, method_name: str, *args, **kwargs) -> Tuple[Any, float]:
        """
        Benchmark any method in this class.
        Returns (result, execution_time_seconds).
        """
        start_time = time.time()

        method = getattr(cls, method_name)
        result = method(*args, **kwargs)

        end_time = time.time()
        execution_time = end_time - start_time

        return result, execution_time
