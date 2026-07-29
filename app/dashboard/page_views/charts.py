"""
Dashboard 圖表元件

加深資料線／長條、格線與座標軸，提升淺色背景下的可讀性。
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

_LINE_COLOR = "#1E3A8A"
_BAR_COLOR = "#166534"
_AXIS_COLOR = "#111827"
_GRID_COLOR = "#4B5563"
_DOMAIN_COLOR = "#374151"
_LABEL_COLOR = "#111827"


def _axis_x(*, label_angle: int = -90, grid: bool = False) -> alt.Axis:
    return alt.Axis(
        labelAngle=label_angle,
        labelColor=_LABEL_COLOR,
        titleColor=_AXIS_COLOR,
        labelFontWeight=600,
        titleFontWeight=700,
        grid=grid,
        gridColor=_GRID_COLOR,
        domainColor=_DOMAIN_COLOR,
        tickColor=_DOMAIN_COLOR,
        domainWidth=1.5,
        tickWidth=1.25,
    )


def _axis_y(*, grid: bool = True) -> alt.Axis:
    return alt.Axis(
        labelColor=_LABEL_COLOR,
        titleColor=_AXIS_COLOR,
        labelFontWeight=600,
        titleFontWeight=700,
        grid=grid,
        gridColor=_GRID_COLOR,
        gridOpacity=0.85,
        domainColor=_DOMAIN_COLOR,
        tickColor=_DOMAIN_COLOR,
        domainWidth=1.5,
        tickWidth=1.25,
    )


def render_dark_line_chart(
    data: pd.Series | pd.DataFrame,
    *,
    height: int = 280,
) -> None:
    """渲染加深線條與格線的折線圖。"""
    if isinstance(data, pd.Series):
        chart_df = data.reset_index()
    else:
        chart_df = data.reset_index()

    x_col = chart_df.columns[0]
    y_col = chart_df.columns[-1]

    chart = (
        alt.Chart(chart_df)
        .mark_line(
            color=_LINE_COLOR,
            strokeWidth=3.5,
            point=alt.OverlayMarkDef(color=_LINE_COLOR, size=65, filled=True),
        )
        .encode(
            x=alt.X(f"{x_col}:O", axis=_axis_x()),
            y=alt.Y(f"{y_col}:Q", axis=_axis_y()),
        )
        .properties(height=height)
        .configure_view(stroke=_DOMAIN_COLOR)
        .configure_axis(labelColor=_LABEL_COLOR, titleColor=_AXIS_COLOR)
    )
    st.altair_chart(chart, use_container_width=True)


def render_dark_bar_chart(
    data: pd.Series | pd.DataFrame,
    *,
    height: int = 420,
    x_title: str | None = None,
    y_title: str | None = None,
) -> None:
    """渲染加深座標軸文字與格線的長條圖。"""
    if isinstance(data, pd.Series):
        chart_df = data.rename_axis(data.index.name or "index").reset_index()
        chart_df.columns = [str(chart_df.columns[0]), str(data.name or "value")]
    else:
        chart_df = data.copy()
        if chart_df.index.name is not None or not isinstance(chart_df.index, pd.RangeIndex):
            # index 為類別（如關鍵詞）
            if chart_df.shape[1] == 1:
                chart_df = chart_df.reset_index()
            elif not any(col in ("關鍵詞", "index") for col in chart_df.columns):
                # 已是兩欄以上且含類別欄，維持原樣
                pass

    if chart_df.shape[1] < 2:
        chart_df = chart_df.reset_index()

    x_col = str(chart_df.columns[0])
    y_col = str(chart_df.columns[1])

    chart = (
        alt.Chart(chart_df)
        .mark_bar(color=_BAR_COLOR, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X(
                f"{x_col}:N",
                sort=None,
                title=x_title if x_title is not None else x_col,
                axis=_axis_x(label_angle=-90),
            ),
            y=alt.Y(
                f"{y_col}:Q",
                title=y_title if y_title is not None else y_col,
                axis=_axis_y(),
            ),
            tooltip=[
                alt.Tooltip(f"{x_col}:N", title=x_col),
                alt.Tooltip(f"{y_col}:Q", title=y_col, format=","),
            ],
        )
        .properties(height=height)
        .configure_view(stroke=_DOMAIN_COLOR)
        .configure_axis(
            labelColor=_LABEL_COLOR,
            titleColor=_AXIS_COLOR,
            gridColor=_GRID_COLOR,
            domainColor=_DOMAIN_COLOR,
            tickColor=_DOMAIN_COLOR,
        )
    )
    st.altair_chart(chart, use_container_width=True)
