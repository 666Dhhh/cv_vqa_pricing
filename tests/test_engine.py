import pytest
from src.engine import QuantumPricingEngine

@pytest.fixture
def sample_config():
    return {
        'market': {'S0': 100.0, 'r': 0.05, 'sigma': 0.2, 'T': 1.0, 'K': 100.0},
        'quantum': {'num_wires': 2, 'learning_rate': 0.15, 'max_epochs': 40},
        'simulation': {'monte_carlo_samples': 50000, 'seed': 42}
    }

def test_bs_price_accuracy(sample_config):
    engine = QuantumPricingEngine(sample_config)
    bs_p = engine.black_scholes_price(100.0, 100.0, 0.05, 0.2, 1.0)
    assert round(bs_p, 4) == 10.4506

def test_vqa_pricing_zero_noise(sample_config):
    engine = QuantumPricingEngine(sample_config)
    res = engine.train_and_price(loss_rate=0.0)
    assert res['relative_error_pct'] < 0.1
