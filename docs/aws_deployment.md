# AWS 部署架構文件

## AI 詐騙進化預測系統 — 雲端部署指南

---

## 1. 建議 AWS 架構概覽

```
                          ┌─────────────────────────────────────────────────┐
                          │                   AWS 雲端環境                    │
                          │                                                   │
  使用者 ──► CloudFront ──► ALB (Application Load Balancer)                  │
                          │    │                                              │
                          │    ├──► EC2 Auto Scaling Group                   │
                          │    │       ├── API Gateway (FastAPI)              │
                          │    │       ├── Dashboard (Streamlit)              │
                          │    │       └── Pattern Analyzer / Prediction      │
                          │    │                                              │
                          │    ├──► RDS (PostgreSQL)                         │
                          │    ├──► ElastiCache (Redis)                      │
                          │    ├──► S3 (模型檔案 / 資料集 / 靜態資源)          │
                          │    └──► EC2 (Qdrant 向量資料庫)                   │
                          │                                                   │
                          │  監控：CloudWatch + SNS 告警                      │
                          │  安全：VPC + Security Groups + IAM + Secrets Mgr  │
                          └─────────────────────────────────────────────────┘
```

### 核心服務清單

| AWS 服務 | 用途 | 對應本地服務 |
|---|---|---|
| EC2 (Auto Scaling) | 執行 API Gateway、Dashboard、分析模組 | `docker-compose` 應用層 |
| RDS for PostgreSQL | 儲存案例資料、存取日誌、模型版本 | `postgres` 容器 |
| ElastiCache for Redis | API 速率限制、Dashboard 快取 | `redis` 容器 |
| S3 | 模型檔案儲存、資料集備份、靜態資源 | 本地 `data/` 目錄 |
| EC2 (獨立) | Qdrant 向量資料庫（目前無托管服務） | `qdrant` 容器 |
| ALB | 負載均衡、SSL 終止 | 本地 `localhost` |
| CloudFront | CDN 加速、靜態資源快取 | 無對應 |
| VPC | 網路隔離 | Docker 內部網路 `scam_network` |
| Secrets Manager | 管理資料庫密碼、API 金鑰 | `.env` 檔案 |
| CloudWatch | 日誌收集、效能監控、告警 | 本地 logging |

---

## 2. 本地 docker-compose 與 AWS 服務對應關係

### 2.1 資料庫層

| docker-compose 服務 | AWS 對應服務 | 規格建議 | 說明 |
|---|---|---|---|
| `postgres:16-alpine` | **RDS for PostgreSQL 16** | `db.t3.medium`（開發）/ `db.r6g.large`（生產） | 啟用 Multi-AZ 確保高可用性；啟用自動備份（保留 7 天） |
| `redis:7-alpine` | **ElastiCache for Redis 7** | `cache.t3.micro`（開發）/ `cache.r6g.large`（生產） | 使用 Cluster Mode Disabled 單節點或 Replication Group |
| `qdrant:v1.9.0` | **EC2 + EBS** | `t3.large` + 100GB gp3 EBS | Qdrant 目前無 AWS 托管服務，需自行在 EC2 上部署 |

### 2.2 應用層

| 本地執行方式 | AWS 對應方式 | 說明 |
|---|---|---|
| `uvicorn app/api_gateway/main.py` | EC2 Auto Scaling Group | 使用 Launch Template 定義 AMI 與啟動腳本 |
| `streamlit run app/dashboard/streamlit_app.py` | EC2 (獨立實例或同一 ASG) | 建議獨立部署，透過 ALB 路由 `/dashboard/*` |
| 本地 `.env` 環境變數 | AWS Secrets Manager + Parameter Store | 敏感資訊（DB 密碼、API 金鑰）存入 Secrets Manager |

### 2.3 網路對應

| docker-compose 設定 | AWS 對應設定 |
|---|---|
| `networks: scam_network` | VPC 內部子網路（Private Subnet） |
| `ports: "5432:5432"` | RDS 僅在 Private Subnet，不對外開放 |
| `ports: "6379:6379"` | ElastiCache 僅在 Private Subnet |
| `ports: "6333:6333"` | Qdrant EC2 在 Private Subnet，透過 Security Group 限制存取 |

---

## 3. 部署步驟（概念性說明）

### 步驟 1：建立 VPC 與網路架構

1. 建立 VPC（建議 CIDR：`10.0.0.0/16`）
2. 建立 Public Subnet（2 個可用區，供 ALB 使用）
3. 建立 Private Subnet（2 個可用區，供 EC2、RDS、ElastiCache 使用）
4. 建立 Internet Gateway 並附加至 VPC
5. 設定 Route Table：Public Subnet 路由至 Internet Gateway

### 步驟 2：建立安全群組（Security Groups）

```
ALB Security Group:
  - Inbound: 443 (HTTPS) from 0.0.0.0/0
  - Inbound: 80 (HTTP) from 0.0.0.0/0 → 重導向至 443

EC2 Application Security Group:
  - Inbound: 8000 (FastAPI) from ALB Security Group
  - Inbound: 8501 (Streamlit) from ALB Security Group
  - Inbound: 22 (SSH) from 管理員 IP（或透過 SSM Session Manager）

RDS Security Group:
  - Inbound: 5432 (PostgreSQL) from EC2 Application Security Group

ElastiCache Security Group:
  - Inbound: 6379 (Redis) from EC2 Application Security Group

Qdrant Security Group:
  - Inbound: 6333 (HTTP) from EC2 Application Security Group
  - Inbound: 6334 (gRPC) from EC2 Application Security Group
```

### 步驟 3：建立 RDS PostgreSQL

1. 選擇 PostgreSQL 16 引擎
2. 部署至 Private Subnet（Multi-AZ 建議開啟）
3. 設定資料庫名稱：`scam_prediction`
4. 將密碼存入 AWS Secrets Manager
5. 執行初始化 SQL（`docker/postgres/init.sql`）

### 步驟 4：建立 ElastiCache Redis

1. 選擇 Redis 7.x 引擎
2. 部署至 Private Subnet
3. 設定 `maxmemory-policy: allkeys-lru`（與本地設定一致）
4. 記錄 Primary Endpoint 供應用程式連線

### 步驟 5：建立 S3 儲存桶

```bash
# 建立模型儲存桶
aws s3 mb s3://scam-prediction-models --region ap-northeast-1

# 建立資料集儲存桶
aws s3 mb s3://scam-prediction-datasets --region ap-northeast-1

# 上傳示範資料
aws s3 cp data/sample_scam_cases.csv s3://scam-prediction-datasets/
```

### 步驟 6：建立 EC2 應用伺服器

1. 選擇 Amazon Linux 2023 AMI
2. 建立 Launch Template，包含以下 User Data 啟動腳本：

```bash
#!/bin/bash
# 安裝相依套件
yum update -y
yum install -y python3.11 python3.11-pip git

# 取得應用程式碼（從 CodeCommit 或 S3）
aws s3 cp s3://scam-prediction-app/app.tar.gz /opt/app.tar.gz
tar -xzf /opt/app.tar.gz -C /opt/

# 安裝 Python 套件
cd /opt/app
pip3.11 install -r requirements.txt

# 從 Secrets Manager 取得環境變數
SECRET=$(aws secretsmanager get-secret-value \
  --secret-id scam-prediction/prod \
  --query SecretString --output text)

# 啟動 API Gateway
export DATABASE_URL=$(echo $SECRET | python3 -c "import sys,json; print(json.load(sys.stdin)['DATABASE_URL'])")
uvicorn app.api_gateway.main:app --host 0.0.0.0 --port 8000 &

# 啟動 Streamlit Dashboard
streamlit run app/dashboard/streamlit_app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 &
```

3. 建立 Auto Scaling Group，設定最小 1 台、最大 4 台
4. 設定 CPU 使用率 > 70% 時自動擴展

### 步驟 7：建立 Application Load Balancer

1. 建立 ALB，部署至 Public Subnet
2. 建立 Target Group（EC2 實例，Port 8000）
3. 設定 Listener Rules：
   - `/api/*` → API Gateway Target Group (Port 8000)
   - `/dashboard/*` → Dashboard Target Group (Port 8501)
   - `/` → 預設導向 Dashboard
4. 申請 ACM 憑證並設定 HTTPS Listener

### 步驟 8：設定 CloudWatch 監控

```bash
# 建立 CPU 使用率告警
aws cloudwatch put-metric-alarm \
  --alarm-name "ScamPrediction-HighCPU" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --period 300 \
  --alarm-actions arn:aws:sns:ap-northeast-1:ACCOUNT_ID:scam-prediction-alerts
```

---

## 4. 預估費用說明

以下費用以 **ap-northeast-1（東京）** 區域為基準，實際費用依使用量而定。

### 4.1 開發 / 測試環境（每月估算）

| 服務 | 規格 | 預估月費（USD） |
|---|---|---|
| EC2 t3.medium × 1 | 2 vCPU / 4GB RAM | ~$30 |
| RDS db.t3.micro | PostgreSQL 16，20GB | ~$15 |
| ElastiCache cache.t3.micro | Redis 7，單節點 | ~$12 |
| EC2 t3.small（Qdrant） | 2 vCPU / 2GB RAM + 50GB EBS | ~$20 |
| S3 | 50GB 儲存 + 請求費用 | ~$2 |
| ALB | 每月固定費 + LCU | ~$20 |
| **合計** | | **~$99 / 月** |

### 4.2 生產環境（每月估算）

| 服務 | 規格 | 預估月費（USD） |
|---|---|---|
| EC2 t3.large × 2（ASG） | 2 vCPU / 8GB RAM，Multi-AZ | ~$120 |
| RDS db.r6g.large（Multi-AZ） | PostgreSQL 16，100GB | ~$200 |
| ElastiCache cache.r6g.large | Redis 7，Replication Group | ~$120 |
| EC2 t3.large（Qdrant） | 2 vCPU / 8GB RAM + 200GB EBS | ~$80 |
| S3 | 500GB 儲存 + 請求費用 | ~$15 |
| ALB | 每月固定費 + LCU | ~$30 |
| CloudFront | 1TB 流量 | ~$85 |
| CloudWatch | 日誌 + 指標 | ~$20 |
| **合計** | | **~$670 / 月** |

### 4.3 費用優化建議

- **使用 Reserved Instances**：對 EC2 和 RDS 購買 1 年期 Reserved Instance，可節省約 30-40% 費用
- **Spot Instances**：非關鍵的批次處理任務（如模型訓練）可使用 Spot Instance，節省約 70% 費用
- **S3 Intelligent-Tiering**：對不常存取的歷史資料啟用 Intelligent-Tiering，自動降低儲存成本
- **CloudWatch Logs 保留期限**：設定適當的日誌保留期限（建議 30-90 天），避免無限累積費用
- **Auto Scaling 排程**：非上班時間（夜間、週末）縮減 EC2 實例數量

---

## 5. 安全性注意事項

- 所有資料庫（RDS、ElastiCache、Qdrant）僅部署於 Private Subnet，不對外開放
- 使用 AWS Secrets Manager 管理所有敏感憑證，禁止將密碼寫入程式碼或環境變數檔案
- 啟用 RDS 加密（at-rest）與傳輸加密（SSL/TLS）
- 定期輪換 API 金鑰與資料庫密碼
- 啟用 AWS CloudTrail 記錄所有 API 操作
- 使用 IAM Role 而非 IAM User 授權 EC2 存取 S3 和 Secrets Manager
