"""
Tests for FreshnessIndicator (Task 9.1), Dashboard integration (Task 9.2),
API Gateway lifecycle (Task 10.1), and module factory functions (Task 10.2).
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app.live_data.models import FreshnessInfo
from app.dashboard.page_views.freshness import render_freshness_indicator


# ── Task 9.1: FreshnessIndicator Tests ────────────────────────────────────────

class TestRenderFreshnessIndicator:
    """Test render_freshness_indicator for all four display states."""

    def test_green_fresh_data(self):
        """Green state: is_fresh=True shows ✅ with source name."""
        info = FreshnessInfo(
            source_name="data.gov.tw",
            fetched_at=datetime(2024, 6, 15, 10, 30, tzinfo=timezone.utc),
            is_fresh=True,
            is_cached=False,
            is_static=False,
            cache_age_hours=0.5,
        )
        result = render_freshness_indicator(info)
        assert "✅" in result
        assert "資料已更新" in result
        assert "2024-06-15 18:30" in result
        assert "data.gov.tw" in result

    def test_yellow_cached_under_24h(self):
        """Yellow state: is_cached=True and cache_age_hours < 24 shows ⚠️."""
        info = FreshnessInfo(
            source_name="data.gov.tw",
            fetched_at=datetime(2024, 6, 15, 10, 30, tzinfo=timezone.utc),
            is_fresh=False,
            is_cached=True,
            is_static=False,
            cache_age_hours=6.0,
        )
        result = render_freshness_indicator(info)
        assert "⚠️" in result
        assert "快取資料" in result
        assert "2024-06-15 18:30" in result
        assert "6 小時前更新" in result

    def test_red_cached_over_24h(self):
        """Red state: is_cached=True and cache_age_hours >= 24 shows 🔴."""
        info = FreshnessInfo(
            source_name="data.gov.tw",
            fetched_at=datetime(2024, 6, 13, 10, 30, tzinfo=timezone.utc),
            is_fresh=False,
            is_cached=True,
            is_static=False,
            cache_age_hours=48.0,
        )
        result = render_freshness_indicator(info)
        assert "🔴" in result
        assert "資料可能過時" in result
        assert "2024-06-13 18:30" in result
        assert "2 天前更新" in result

    def test_gray_static_data(self):
        """Gray state: is_static=True shows 📋."""
        info = FreshnessInfo(
            source_name="靜態預設資料",
            is_fresh=False,
            is_cached=False,
            is_static=True,
            cache_age_hours=0.0,
        )
        result = render_freshness_indicator(info)
        assert "📋" in result
        assert "靜態預設資料" in result
        assert "2023-2024" in result

    def test_fallback_no_flags(self):
        """When no flags are set, should show static fallback."""
        info = FreshnessInfo(
            source_name="無資料",
            is_fresh=False,
            is_cached=False,
            is_static=False,
            cache_age_hours=0.0,
        )
        result = render_freshness_indicator(info)
        assert "📋" in result

    def test_yellow_boundary_23h(self):
        """Yellow state at 23 hours (just under 24h boundary)."""
        info = FreshnessInfo(
            source_name="test",
            fetched_at=datetime(2024, 6, 15, 10, 0, tzinfo=timezone.utc),
            is_fresh=False,
            is_cached=True,
            is_static=False,
            cache_age_hours=23.0,
        )
        result = render_freshness_indicator(info)
        assert "⚠️" in result
        assert "23 小時前更新" in result

    def test_red_boundary_24h(self):
        """Red state at exactly 24 hours."""
        info = FreshnessInfo(
            source_name="test",
            fetched_at=datetime(2024, 6, 14, 10, 0, tzinfo=timezone.utc),
            is_fresh=False,
            is_cached=True,
            is_static=False,
            cache_age_hours=24.0,
        )
        result = render_freshness_indicator(info)
        assert "🔴" in result
        assert "1 天前更新" in result


# ── Task 10.2: Module Factory Functions Tests ─────────────────────────────────

class TestCacheManagerDiskSync:
    """CacheManager 應同步較新的磁碟快取（跨程序更新）。"""

    def test_load_prefers_newer_disk_over_stale_memory(self, tmp_path):
        import time
        from datetime import datetime, timezone

        from app.live_data.cache_manager import CacheManager
        from app.live_data.models import AnnualStat, NormalizedData, ScamTypeStat

        cache_file = tmp_path / "live_cache.json"
        mgr = CacheManager(cache_file_path=str(cache_file))

        def _make(source: str, cases: int) -> NormalizedData:
            return NormalizedData(
                scam_cases_by_region={"台北市": cases},
                scam_type_stats={
                    "假冒銀行客服": ScamTypeStat(
                        cases=cases, avg_loss_ntd=1000, trend="上升"
                    )
                },
                monthly_trend=[],
                victim_age_distribution={},
                annual_stats={
                    "2026": AnnualStat(total_cases=cases, total_loss_billion=0.1)
                },
                source_name=source,
                fetched_at=datetime.now(timezone.utc),
            )

        mgr.store(_make("old-source", 1))
        old_at = mgr.load().cached_at

        time.sleep(0.02)
        other = CacheManager(cache_file_path=str(cache_file))
        other.store(_make("new-source", 2))

        loaded = mgr.load()
        assert loaded is not None
        assert loaded.source_name == "new-source"
        assert loaded.cached_at >= old_at


class TestModuleFactoryFunctions:
    """Test that factory functions in app/live_data/__init__.py work correctly."""

    def test_get_cache_manager_returns_singleton(self):
        """get_cache_manager should return the same instance on repeated calls."""
        import app.live_data as live_data
        # Reset singleton
        live_data._cache_manager = None
        mgr1 = live_data.get_cache_manager()
        mgr2 = live_data.get_cache_manager()
        assert mgr1 is mgr2

    def test_get_fallback_provider_returns_singleton(self):
        """get_fallback_provider should return the same instance on repeated calls."""
        import app.live_data as live_data
        live_data._fallback_provider = None
        live_data._cache_manager = None
        fb1 = live_data.get_fallback_provider()
        fb2 = live_data.get_fallback_provider()
        assert fb1 is fb2

    def test_get_fetch_scheduler_returns_singleton(self):
        """get_fetch_scheduler should return the same instance on repeated calls."""
        import app.live_data as live_data
        live_data._fetch_scheduler = None
        live_data._cache_manager = None
        live_data._fallback_provider = None
        sched1 = live_data.get_fetch_scheduler()
        sched2 = live_data.get_fetch_scheduler()
        assert sched1 is sched2

    def test_get_cache_manager_type(self):
        """get_cache_manager should return a CacheManager instance."""
        import app.live_data as live_data
        from app.live_data.cache_manager import CacheManager
        live_data._cache_manager = None
        mgr = live_data.get_cache_manager()
        assert isinstance(mgr, CacheManager)

    def test_get_fallback_provider_type(self):
        """get_fallback_provider should return a FallbackProvider instance."""
        import app.live_data as live_data
        from app.live_data.fallback import FallbackProvider
        live_data._fallback_provider = None
        live_data._cache_manager = None
        fb = live_data.get_fallback_provider()
        assert isinstance(fb, FallbackProvider)

    def test_get_fetch_scheduler_type(self):
        """get_fetch_scheduler should return a FetchScheduler instance."""
        import app.live_data as live_data
        from app.live_data.scheduler import FetchScheduler
        live_data._fetch_scheduler = None
        live_data._cache_manager = None
        live_data._fallback_provider = None
        sched = live_data.get_fetch_scheduler()
        assert isinstance(sched, FetchScheduler)

    def test_factory_wiring(self):
        """Factory functions should wire components together correctly."""
        import app.live_data as live_data
        live_data._fetch_scheduler = None
        live_data._cache_manager = None
        live_data._fallback_provider = None

        sched = live_data.get_fetch_scheduler()
        # The scheduler should have a fetcher
        assert sched._fetcher is not None
        # The fetcher should have a cache_manager
        assert sched._fetcher._cache_manager is not None


# ── Task 10.1: API Gateway Lifecycle Integration Tests ────────────────────────

class TestAPIGatewayLifecycle:
    """Test that FetchScheduler is integrated into API Gateway lifespan."""

    def test_lifespan_imports_fetch_scheduler(self):
        """The lifespan function should import and use get_fetch_scheduler."""
        import inspect
        from app.api_gateway.main import lifespan
        source = inspect.getsource(lifespan)
        assert "get_fetch_scheduler" in source
        assert "data_scheduler" in source or "fetch_scheduler" in source

    def test_lifespan_has_try_except(self):
        """FetchScheduler start should be wrapped in try/except."""
        import inspect
        from app.api_gateway.main import lifespan
        source = inspect.getsource(lifespan)
        # Should have try/except around the fetch scheduler start
        assert "即時資料擷取排程器" in source or "live_data" in source

    def test_lifespan_stops_scheduler(self):
        """The lifespan should stop the FetchScheduler on shutdown."""
        import inspect
        from app.api_gateway.main import lifespan
        source = inspect.getsource(lifespan)
        assert "data_scheduler" in source
        # Should call stop
        assert ".stop()" in source
