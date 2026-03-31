"""
Dashboard 邏輯測試模組

涵蓋熱詞排行榜、沙盤推演、風險地圖與快取降級邏輯的單元測試與屬性測試。

屬性測試：
- 屬性 14：熱詞排行榜排序正確性（需求 4.1）
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st

from app.dashboard.pages.hotwords import compute_hotword_ranking, get_hotword_page_data
from app.dashboard.pages.sandbox import (
    SandboxParams,
    run_sandbox_simulation,
    validate_sandbox_params,
)
from app.dashboard.pages.risk_map import (
    RiskMapEntry,
    build_risk_map,
    compute_risk_index,
    get_risk_map_summary,
)
from app.dashboard.pages.cache import (
    CacheEntry,
    DashboardCache,
    format_cache_status,
)


# ── 熱詞排行榜單元測試 ────────────────────────────────────────────────────────

class TestComputeHotwordRanking:
    """compute_hotword_ranking 單元測試"""

    def test_empty_dict_returns_empty_list(self) -> None:
        """空字典應回傳空列表"""
        assert compute_hotword_ranking({}) == []

    def test_single_keyword(self) -> None:
        """單一關鍵詞應正確回傳"""
        result = compute_hotword_ranking({"詐騙": 10})
        assert result == ["詐騙"]

    def test_sorted_by_frequency_descending(self) -> None:
        """應依頻率降序排列"""
        freq = {"轉帳": 50, "詐騙": 100, "銀行": 30}
        result = compute_hotword_ranking(freq)
        assert result == ["詐騙", "轉帳", "銀行"]

    def test_max_20_results(self) -> None:
        """結果長度不超過 20"""
        freq = {f"詞{i}": i for i in range(1, 31)}
        result = compute_hotword_ranking(freq)
        assert len(result) <= 20

    def test_exactly_20_keywords(self) -> None:
        """恰好 20 個關鍵詞時全部回傳"""
        freq = {f"詞{i}": i for i in range(1, 21)}
        result = compute_hotword_ranking(freq)
        assert len(result) == 20

    def test_top_20_are_highest_frequency(self) -> None:
        """回傳的應為頻率最高的前 20 個"""
        freq = {f"詞{i}": i for i in range(1, 31)}
        result = compute_hotword_ranking(freq)
        # 頻率最高的是 詞30, 詞29, ..., 詞11
        assert "詞30" in result
        assert "詞11" in result
        assert "詞10" not in result

    def test_zero_frequency_excluded(self) -> None:
        """頻率為 0 的關鍵詞應被排除"""
        freq = {"詐騙": 10, "空詞": 0}
        result = compute_hotword_ranking(freq)
        assert "空詞" not in result
        assert "詐騙" in result

    def test_negative_frequency_excluded(self) -> None:
        """負頻率的關鍵詞應被排除"""
        freq = {"詐騙": 10, "負詞": -5}
        result = compute_hotword_ranking(freq)
        assert "負詞" not in result

    def test_non_numeric_frequency_excluded(self) -> None:
        """非數值頻率的關鍵詞應被排除"""
        freq = {"詐騙": 10, "壞資料": "abc"}
        result = compute_hotword_ranking(freq)
        assert "壞資料" not in result
        assert "詐騙" in result

    def test_same_frequency_stable_order(self) -> None:
        """相同頻率時應依字典序排列（穩定性）"""
        freq = {"乙": 10, "甲": 10, "丙": 10}
        result = compute_hotword_ranking(freq)
        assert len(result) == 3
        # 相同頻率時依字典序升序
        assert result == sorted(result)

    def test_float_frequency(self) -> None:
        """浮點數頻率應正確處理"""
        freq = {"詐騙": 10.5, "轉帳": 8.3}
        result = compute_hotword_ranking(freq)
        assert result[0] == "詐騙"
        assert result[1] == "轉帳"


class TestGetHotwordPageData:
    """get_hotword_page_data 單元測試"""

    def test_returns_correct_structure(self) -> None:
        """應回傳包含 ranking、total_keywords、displayed_count 的字典"""
        freq = {"詐騙": 100, "轉帳": 50}
        result = get_hotword_page_data(freq)
        assert "ranking" in result
        assert "total_keywords" in result
        assert "displayed_count" in result

    def test_total_keywords_matches_input(self) -> None:
        """total_keywords 應等於輸入字典的大小"""
        freq = {f"詞{i}": i for i in range(1, 11)}
        result = get_hotword_page_data(freq)
        assert result["total_keywords"] == 10

    def test_displayed_count_matches_ranking_length(self) -> None:
        """displayed_count 應等於 ranking 列表的長度"""
        freq = {f"詞{i}": i for i in range(1, 25)}
        result = get_hotword_page_data(freq)
        assert result["displayed_count"] == len(result["ranking"])
        assert result["displayed_count"] <= 20


# ── 屬性測試：屬性 14 ─────────────────────────────────────────────────────────

class TestHotwordRankingProperties:
    """
    屬性 14：熱詞排行榜排序正確性

    **Validates: Requirements 4.1**

    對於任意關鍵詞頻率資料集，熱詞排行計算函數輸出的排行榜
    應按頻率降序排列，且長度 <= 20。
    """

    @h_settings(max_examples=20)
    @given(
        keyword_freq=st.dictionaries(
            keys=st.text(min_size=1, max_size=10).filter(lambda s: s.strip()),
            values=st.integers(min_value=1, max_value=10000),
            min_size=0,
            max_size=50,
        )
    )
    def test_hotword_ranking_order(self, keyword_freq: dict) -> None:
        """
        屬性 14：熱詞排行榜排序正確性

        **Validates: Requirements 4.1**

        對於任意關鍵詞頻率資料集，排行榜應按頻率降序排列，且長度 <= 20。
        """
        # Feature: ai-scam-evolution-prediction, Property 14: 熱詞排行榜排序正確性
        result = compute_hotword_ranking(keyword_freq)

        # 長度不超過 20
        assert len(result) <= 20

        # 結果中的詞應都在輸入字典中
        for word in result:
            assert word in keyword_freq

        # 依頻率降序排列：相鄰兩個詞，前者頻率 >= 後者頻率
        for i in range(len(result) - 1):
            freq_current = keyword_freq[result[i]]
            freq_next = keyword_freq[result[i + 1]]
            assert freq_current >= freq_next, (
                f"排行榜排序錯誤：{result[i]}（頻率={freq_current}）"
                f"應排在 {result[i+1]}（頻率={freq_next}）之前"
            )

    @h_settings(max_examples=20)
    @given(
        keyword_freq=st.dictionaries(
            keys=st.text(min_size=1, max_size=10).filter(lambda s: s.strip()),
            values=st.integers(min_value=1, max_value=10000),
            min_size=21,
            max_size=100,
        )
    )
    def test_hotword_ranking_max_length(self, keyword_freq: dict) -> None:
        """
        屬性 14（補充）：超過 20 個關鍵詞時，結果長度應恰好為 20

        **Validates: Requirements 4.1**
        """
        # Feature: ai-scam-evolution-prediction, Property 14: 熱詞排行榜排序正確性
        result = compute_hotword_ranking(keyword_freq)
        assert len(result) == 20

    @h_settings(max_examples=20)
    @given(
        keyword_freq=st.dictionaries(
            keys=st.text(min_size=1, max_size=10).filter(lambda s: s.strip()),
            values=st.integers(min_value=1, max_value=10000),
            min_size=1,
            max_size=20,
        )
    )
    def test_hotword_ranking_contains_top_words(self, keyword_freq: dict) -> None:
        """
        屬性 14（補充）：結果應包含頻率最高的詞

        **Validates: Requirements 4.1**
        """
        # Feature: ai-scam-evolution-prediction, Property 14: 熱詞排行榜排序正確性
        result = compute_hotword_ranking(keyword_freq)

        if not keyword_freq:
            assert result == []
            return

        # 頻率最高的詞應出現在結果中
        max_freq = max(keyword_freq.values())
        top_words = [w for w, f in keyword_freq.items() if f == max_freq]
        assert any(w in result for w in top_words), (
            f"頻率最高的詞 {top_words} 應出現在排行榜中，但結果為 {result}"
        )


# ── 沙盤推演單元測試 ──────────────────────────────────────────────────────────

class TestSandboxSimulation:
    """沙盤推演邏輯單元測試"""

    def test_validate_valid_params(self) -> None:
        """合法參數應通過驗證"""
        params = SandboxParams(
            scenario_type="假冒銀行客服",
            target_audience="中老年族群",
        )
        errors = validate_sandbox_params(params)
        assert errors == []

    def test_validate_empty_scenario_type(self) -> None:
        """空的 scenario_type 應回傳錯誤"""
        params = SandboxParams(scenario_type="", target_audience="中老年族群")
        errors = validate_sandbox_params(params)
        assert any("scenario_type" in e for e in errors)

    def test_validate_invalid_risk_level_filter(self) -> None:
        """不合法的 risk_level_filter 應回傳錯誤"""
        params = SandboxParams(
            scenario_type="投資詐騙",
            target_audience="年輕族群",
            risk_level_filter="極高",
        )
        errors = validate_sandbox_params(params)
        assert any("risk_level_filter" in e for e in errors)

    def test_validate_invalid_time_window(self) -> None:
        """超出範圍的 time_window_days 應回傳錯誤"""
        params = SandboxParams(
            scenario_type="投資詐騙",
            target_audience="年輕族群",
            time_window_days=0,
        )
        errors = validate_sandbox_params(params)
        assert any("time_window_days" in e for e in errors)

    def test_run_simulation_basic(self) -> None:
        """基本沙盤推演應回傳合法結果"""
        params = SandboxParams(
            scenario_type="假冒銀行客服",
            target_audience="中老年族群",
        )
        result = run_sandbox_simulation(params)
        assert result.scenario_type == "假冒銀行客服"
        assert result.target_audience == "中老年族群"
        assert result.predicted_risk_level in {"高", "中", "低"}
        assert len(result.predicted_features) >= 1
        assert 0.0 <= result.confidence_score <= 1.0

    def test_run_simulation_invalid_params_raises(self) -> None:
        """不合法參數應拋出 ValueError"""
        params = SandboxParams(scenario_type="", target_audience="")
        with pytest.raises(ValueError):
            run_sandbox_simulation(params)

    def test_run_simulation_with_risk_vectors(self) -> None:
        """提供 Risk_Vector 資料時應整合推演"""
        params = SandboxParams(
            scenario_type="投資詐騙",
            target_audience="年輕族群",
        )
        risk_vectors = [
            {
                "scam_cluster_label": "投資詐騙",
                "high_risk_features": ["高報酬誘惑", "假冒名人"],
                "risk_score": 0.8,
                "target_audience": "年輕族群",
            }
        ]
        result = run_sandbox_simulation(params, risk_vectors=risk_vectors)
        assert "高報酬誘惑" in result.predicted_features or "假冒名人" in result.predicted_features


# ── 風險地圖單元測試 ──────────────────────────────────────────────────────────

class TestRiskMap:
    """風險地圖邏輯單元測試"""

    def test_compute_risk_index_empty_vectors(self) -> None:
        """空向量列表應回傳 0.0"""
        result = compute_risk_index([], "中老年族群", "台北市")
        assert result == 0.0

    def test_compute_risk_index_with_data(self) -> None:
        """有資料時應計算平均風險分數"""
        vectors = [
            {"risk_score": 0.8, "target_audience": "", "region": ""},
            {"risk_score": 0.6, "target_audience": "", "region": ""},
        ]
        result = compute_risk_index(vectors, "中老年族群", "台北市")
        assert result == pytest.approx(0.7, abs=0.001)

    def test_build_risk_map_returns_entries(self) -> None:
        """build_risk_map 應回傳包含條目的 RiskMapData"""
        risk_map = build_risk_map(
            risk_vectors=[],
            age_groups=["18-29歲", "30-44歲"],
            regions=["台北市", "新北市"],
        )
        assert len(risk_map.entries) == 4  # 2 年齡層 × 2 地區
        assert risk_map.age_groups == ["18-29歲", "30-44歲"]
        assert risk_map.regions == ["台北市", "新北市"]

    def test_build_risk_map_risk_level_classification(self) -> None:
        """風險等級應依風險指數正確分類"""
        vectors = [{"risk_score": 0.9, "target_audience": "", "region": ""}]
        risk_map = build_risk_map(
            risk_vectors=vectors,
            age_groups=["中老年族群"],
            regions=["台北市"],
        )
        assert risk_map.entries[0].risk_level == "高"
        assert risk_map.overall_risk_level == "高"

    def test_get_risk_map_summary_structure(self) -> None:
        """摘要應包含必要欄位"""
        risk_map = build_risk_map(
            risk_vectors=[],
            age_groups=["18-29歲"],
            regions=["台北市"],
        )
        summary = get_risk_map_summary(risk_map)
        assert "overall_risk_level" in summary
        assert "total_entries" in summary
        assert "high_risk_count" in summary
        assert "medium_risk_count" in summary
        assert "low_risk_count" in summary


# ── 快取降級邏輯單元測試 ──────────────────────────────────────────────────────

class TestDashboardCache:
    """DashboardCache 單元測試"""

    def test_get_nonexistent_key_returns_none(self) -> None:
        """不存在的快取鍵應回傳 None"""
        cache = DashboardCache()
        assert cache.get("nonexistent") is None

    def test_set_and_get(self) -> None:
        """設定後應能讀取快取資料"""
        cache = DashboardCache()
        cache.set("key1", {"data": "test"})
        entry = cache.get("key1")
        assert entry is not None
        assert entry.data == {"data": "test"}

    def test_invalidate_removes_entry(self) -> None:
        """invalidate 應移除快取條目"""
        cache = DashboardCache()
        cache.set("key1", "data")
        cache.invalidate("key1")
        assert cache.get("key1") is None

    def test_clear_removes_all_entries(self) -> None:
        """clear 應清除所有快取"""
        cache = DashboardCache()
        cache.set("key1", "data1")
        cache.set("key2", "data2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_fetch_with_fallback_success(self) -> None:
        """後端可用時應回傳最新資料"""
        cache = DashboardCache()
        fresh_data = {"hotwords": ["詐騙", "轉帳"]}

        data, is_from_cache, cached_at = cache.fetch_with_fallback(
            "hotwords",
            lambda: fresh_data,
        )

        assert data == fresh_data
        assert is_from_cache is False
        assert cached_at is None

    def test_fetch_with_fallback_uses_cache_on_failure(self) -> None:
        """後端不可用時應使用快取降級"""
        cache = DashboardCache()
        cached_data = {"hotwords": ["舊資料"]}
        cache.set("hotwords", cached_data)

        def failing_fetch():
            raise ConnectionError("後端服務不可用")

        data, is_from_cache, cached_at = cache.fetch_with_fallback(
            "hotwords",
            failing_fetch,
        )

        assert data == cached_data
        assert is_from_cache is True
        assert cached_at is not None

    def test_fetch_with_fallback_raises_when_no_cache(self) -> None:
        """後端不可用且無快取時應拋出 RuntimeError"""
        cache = DashboardCache()

        def failing_fetch():
            raise ConnectionError("後端服務不可用")

        with pytest.raises(RuntimeError, match="後端服務不可用且無快取資料"):
            cache.fetch_with_fallback("no_cache_key", failing_fetch)

    def test_cache_entry_is_expired(self) -> None:
        """過期的快取條目應標記為已過期"""
        from datetime import timedelta

        entry = CacheEntry(
            key="test",
            data="data",
            cached_at=datetime.now(timezone.utc) - timedelta(seconds=100),
            ttl_seconds=60,
        )
        assert entry.is_expired is True

    def test_cache_entry_not_expired(self) -> None:
        """未過期的快取條目應標記為未過期"""
        entry = CacheEntry(
            key="test",
            data="data",
            cached_at=datetime.now(timezone.utc),
            ttl_seconds=3600,
        )
        assert entry.is_expired is False

    def test_format_cache_status_fresh_data(self) -> None:
        """最新資料應回傳對應狀態文字"""
        status = format_cache_status(False, None)
        assert "最新" in status

    def test_format_cache_status_stale_data(self) -> None:
        """快取資料應回傳包含更新時間的狀態文字"""
        cached_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        status = format_cache_status(True, cached_at)
        assert "快取" in status
        assert "2024" in status
