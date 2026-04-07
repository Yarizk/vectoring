"""Tests for config module."""
import os
import importlib


def test_stockbit_token_loaded_from_env(monkeypatch):
    """STOCKBIT_TOKEN should be accessible from config."""
    monkeypatch.setenv("STOCKBIT_TOKEN", "test_token_123")
    # Force reimport to pick up new env
    import src.config as config_mod
    importlib.reload(config_mod)
    assert config_mod.STOCKBIT_TOKEN == "test_token_123"


def test_stockbit_token_defaults_to_empty(monkeypatch):
    """STOCKBIT_TOKEN should default to empty string if not set."""
    monkeypatch.delenv("STOCKBIT_TOKEN", raising=False)
    import src.config as config_mod
    importlib.reload(config_mod)
    assert config_mod.STOCKBIT_TOKEN == ""
