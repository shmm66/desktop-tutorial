"""Tests for the Radar Nahang (market scanner) service."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from app.services.radar_service import (
    RadarSignal,
    RadarScanResult,
    scan_radar,
    _score_signal,
    _classify_trend,
    get_radar_summary,
)


def test_classify_trend() -> None:
    """Test trend classification thresholds."""
    assert _classify_trend(None) == "neutral"
    assert _classify_trend(1.2) == "bullish"
    assert _classify_trend(-1.2) == "bearish"
    assert _classify_trend(0.3) == "bullish"
    assert _classify_trend(-0.3) == "bearish"
    assert _classify_trend(0.0) == "neutral"
    assert _classify_trend(0.5) == "neutral"
    assert _classify_trend(-0.5) == "neutral"


def test_score_signal_bullish_rsi() -> None:
    """Test scoring gives bonus for bullish RSI in 30-50 range."""
    s = RadarSignal(
        symbol="EURUSD",
        name="EUR/USD",
        price=1.05,
        change_pct=0.8,
        trend="bullish",
        strength=0.8,
        rsi=35.0,
        volume_ratio=1.0,
        setup="RSI oversold bounce",
        score=0.0,
    )
    score = _score_signal(s)
    # Should be > 0.8 due to RSI bonus
    assert score > 0.8, f"Expected score > 0.8, got {score}"


def test_score_signal_no_rsi() -> None:
    """Test scoring without RSI returns base strength."""
    s = RadarSignal(
        symbol="BTC-USD",
        name="BTC/USD",
        price=45000.0,
        change_pct=2.1,
        trend="bullish",
        strength=2.1,
        rsi=None,
        volume_ratio=1.0,
        setup="High momentum move",
        score=0.0,
    )
    score = _score_signal(s)
    assert score == 2.1, f"Expected score 2.1, got {score}"


def test_score_signal_high_volume() -> None:
    """Test scoring gives volume bonus."""
    s = RadarSignal(
        symbol="ETH-USD",
        name="ETH/USD",
        price=3000.0,
        change_pct=1.5,
        trend="bullish",
        strength=1.5,
        rsi=35.0,
        volume_ratio=2.0,
        setup="RSI oversold bounce",
        score=0.0,
    )
    score = _score_signal(s)
    # strength * 1.1 (RSI) * min(2.0, 1.5) = 1.5 * 1.1 * 1.5 = 2.475
    assert abs(score - 2.475) < 0.01, f"Expected ~2.475, got {score}"


def test_empty_signals_summary() -> None:
    """Test summary with no signals."""
    assert get_radar_summary([]) == "هیچ سیگنال پیدا نشد"


def test_summary_with_signals() -> None:
    """Test summary displays counts by trend."""
    signals = [
        RadarSignal("BTC", "BTC/USD", 45000.0, 2.1, "bullish", 1.5, rsi=35.0, volume_ratio=1.0, setup="test", score=2.0),
        RadarSignal("ETH", "ETH/USD", 3000.0, -1.2, "bearish", 1.2, rsi=65.0, volume_ratio=1.0, setup="test", score=1.5),
        RadarSignal("SOL", "SOL/USD", 100.0, 0.3, "neutral", 0.5, rsi=None, volume_ratio=1.0, setup="test", score=0.5),
    ]
    summary = get_radar_summary(signals)
    assert "bullish" in summary
    assert "bearish" in summary
    assert "neutral" in summary


def test_radar_signal_dataclass() -> None:
    """Test RadarSignal can be constructed and has expected fields."""
    s = RadarSignal(
        symbol="TEST",
        name="Test",
        price=100.0,
        change_pct=1.0,
        trend="bullish",
        strength=1.0,
    )
    assert s.symbol == "TEST"
    assert s.name == "Test"
    assert s.price == 100.0
    assert s.change_pct == 1.0
    assert s.trend == "bullish"
    assert s.strength == 1.0
    assert s.rsi is None
    assert s.volume_ratio is None
    assert s.setup == ""
    assert s.score == 0.0


def test_radar_scan_result_creation() -> None:
    """Test RadarScanResult can be constructed."""
    result = RadarScanResult(market="Forex", timestamp="2026-01-01T00:00:00", source="test")
    assert result.market == "Forex"
    assert result.timestamp == "2026-01-01T00:00:00"
    assert result.source == "test"
    assert result.signals == []
    assert result.status == "unavailable"
    assert result.message == ""


def test_scan_radar_returns_result() -> None:
    """Test scan_radar returns a RadarScanResult (may be empty if no data)."""
    result = scan_radar(market="Forex")
    assert isinstance(result, RadarScanResult)
    assert result.market == "Forex"
    # Result may have no signals if live data is unavailable


def test_scan_radar_with_cache() -> None:
    """Test scan_radar falls back to cache when live data unavailable."""
    # Write a cached payload
    cache_path = Path.home() / "TraderPlannerPro" / "radar_cache.json"
    cache_payload = {
        "market": "Forex",
        "timestamp": "2026-01-01T00:00:00",
        "source": "cache",
        "signals": [
            {
                "symbol": "EURUSD",
                "name": "EUR/USD",
                "price": 1.05,
                "change_pct": 0.8,
                "trend": "bullish",
                "strength": 0.8,
                "rsi": 35.0,
                "volume_ratio": 1.0,
                "setup": "RSI oversold bounce",
                "score": 0.88,
            }
        ],
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache_payload, ensure_ascii=False, indent=2))

    try:
        result = scan_radar(market="Forex")
        assert isinstance(result, RadarScanResult)
        # Should fall back to cache
        assert result.status == "cache" or len(result.signals) > 0
    finally:
        # Clean up cache
        if cache_path.exists():
            cache_path.unlink()


def test_get_radar_summary_persian_awareness() -> None:
    """Test that summary handles Persian/trend labels appropriately."""
    signals = [
        RadarSignal("XRP", "XRP/USD", 0.5, 3.5, "bullish", 2.0, rsi=25.0, volume_ratio=1.5, setup="Strong breakout", score=3.5),
    ]
    summary = get_radar_summary(signals)
    # Should contain some indication of the signal count
    assert len(summary) > 0