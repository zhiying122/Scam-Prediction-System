"""
Dashboard 折線圖元件

加深資料線、格線與座標軸，提升淺色背景下的可讀性。
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

_LINE_COLOR = "#1E40AF"
_AXIS_COLOR = "#374151"
_GRID_COLOR = "#9CA3AF"
_DOMAIN_COLOR = "#6B7280"


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

    axis_x = alt.Axis(
        labelAngle=-90,
        labelColor=_AXIS_COLOR,
        titleColor=_AXIS_COLOR,
        grid=False,
        domainColor=_DOMAIN_COLOR,
        tickColor=_DOMAIN_COLOR,
    )
    axis_y = alt.Axis(
        labelColor=_AXIS_COLOR,
        titleColor=_AXIS_COLOR,
        grid=True,
        gridColor=_GRID_COLOR,
        domainColor=_DOMAIN_COLOR,
        tickColor=_DOMAIN_COLOR,
    )

    chart = (
        alt.Chart(chart_df)
        .mark_line(
            color=_LINE_COLOR,
            strokeWidth=3,
            point=alt.OverlayMarkDef(color=_LINE_COLOR, size=55, filled=True),
        )
        .encode(
            x=alt.X(f"{x_col}:O", axis=axis_x),
            y=alt.Y(f"{y_col}:Q", axis=axis_y),
        )
        .properties(height=height)
        .configure_view(stroke=_DOMAIN_COLOR)
    )
    st.altair_chart(chart, use_container_width=True)
