"""Log line sampling support for logdrift.

Allows users to sample a fraction of matched log lines,
useful for high-volume log streams.
"""

import random
from typing import Optional


class Sampler:
    """Samples log lines based on a given rate."""

    def __init__(self, rate: float, seed: Optional[int] = None):
        """
        Initialize the sampler.

        Args:
            rate: A float between 0.0 and 1.0 representing the fraction
                  of lines to keep. 1.0 keeps all lines, 0.0 keeps none.
            seed: Optional random seed for reproducibility.

        Raises:
            ValueError: If rate is not between 0.0 and 1.0.
        """
        if not (0.0 <= rate <= 1.0):
            raise ValueError(f"Sample rate must be between 0.0 and 1.0, got {rate}")
        self.rate = rate
        self._rng = random.Random(seed)

    def should_keep(self) -> bool:
        """Return True if the current line should be kept based on sample rate."""
        if self.rate == 1.0:
            return True
        if self.rate == 0.0:
            return False
        return self._rng.random() < self.rate


def parse_sample_rate(value: Optional[str]) -> Optional[float]:
    """Parse a sample rate string into a float.

    Args:
        value: A string representation of a float, or None.

    Returns:
        A float between 0.0 and 1.0, or None if value is None.

    Raises:
        ValueError: If the string cannot be parsed or is out of range.
    """
    if value is None:
        return None
    try:
        rate = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid sample rate: {value!r}. Must be a number between 0.0 and 1.0.")
    if not (0.0 <= rate <= 1.0):
        raise ValueError(f"Sample rate {rate} is out of range. Must be between 0.0 and 1.0.")
    return rate


def make_sampler(rate: Optional[float], seed: Optional[int] = None) -> Optional["Sampler"]:
    """Create a Sampler if rate is provided and less than 1.0, else return None."""
    if rate is None or rate == 1.0:
        return None
    return Sampler(rate=rate, seed=seed)
