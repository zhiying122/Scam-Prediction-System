# API 閘道路由套件
# 匯出所有路由模組供 main.py 使用

from app.api_gateway.routers import data, health, predictions, risk_vectors, scam

__all__ = ["health", "scam", "risk_vectors", "data", "predictions"]
