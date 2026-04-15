"""Tests for logdrift/sampler.py"""

import pytest
from logdrift.sampler import Sampler, parse_sample_rate, make_sampler


class TestSampler:
    def test_rate_1_always_keeps(self):
        s = Sampler(rate=1.0)
        assert all(s.should_keep() for _ in range(100))

    def test_rate_0_never_keeps(self):
        s = Sampler(rate=0.0)
        assert not any(s.should_keep() for _ in range(100))

    def test_rate_half_is_roughly_half(self):
        s = Sampler(rate=0.5, seed=42)
        results = [s.should_keep() for _ in range(1000)]
        kept = sum(results)
        assert 400 < kept < 600, f"Expected ~500 kept, got {kept}"

    def test_seed_produces_reproducible_results(self):
        s1 = Sampler(rate=0.3, seed=99)
        s2 = Sampler(rate=0.3, seed=99)
        results1 = [s1.should_keep() for _ in range(50)]
        results2 = [s2.should_keep() for _ in range(50)]
        assert results1 == results2

    def test_invalid_rate_too_high(self):
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            Sampler(rate=1.5)

    def test_invalid_rate_negative(self):
        with pytest.raises(ValueError, match="between 0.0 and 1.0"):
            Sampler(rate=-0.1)


class TestParseSampleRate:
    def test_none_returns_none(self):
        assert parse_sample_rate(None) is None

    def test_valid_string_float(self):
        assert parse_sample_rate("0.5") == 0.5

    def test_zero_string(self):
        assert parse_sample_rate("0") == 0.0

    def test_one_string(self):
        assert parse_sample_rate("1") == 1.0

    def test_invalid_string_raises(self):
        with pytest.raises(ValueError, match="Invalid sample rate"):
            parse_sample_rate("abc")

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError, match="out of range"):
            parse_sample_rate("1.5")

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="out of range"):
            parse_sample_rate("-0.1")


class TestMakeSampler:
    def test_none_rate_returns_none(self):
        assert make_sampler(None) is None

    def test_rate_1_returns_none(self):
        assert make_sampler(1.0) is None

    def test_rate_below_1_returns_sampler(self):
        s = make_sampler(0.5)
        assert isinstance(s, Sampler)
        assert s.rate == 0.5

    def test_rate_0_returns_sampler(self):
        s = make_sampler(0.0)
        assert isinstance(s, Sampler)
        assert s.rate == 0.0

    def test_seed_passed_to_sampler(self):
        s = make_sampler(0.5, seed=7)
        assert s is not None
        results1 = [s.should_keep() for _ in range(20)]
        s2 = make_sampler(0.5, seed=7)
        results2 = [s2.should_keep() for _ in range(20)]
        assert results1 == results2
