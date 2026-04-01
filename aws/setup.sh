#!/bin/bash
# ── AWS 基礎設施初始化腳本 ────────────────────────────────────────────────────
# 首次部署前執行一次，建立 ECS Cluster、CloudWatch Log Groups、Secrets Manager
#
# 使用方式：
#   chmod +x aws/setup.sh
#   ./aws/setup.sh <AWS_ACCOUNT_ID> <AWS_REGION>

set -e

ACCOUNT_ID="${1:?請提供 AWS Account ID}"
REGION="${2:?請提供 AWS Region}"
CLUSTER="scam-prediction-cluster"

echo "======================================================"
echo " 建立 AWS 基礎設施"
echo " Account: $ACCOUNT_ID | Region: $REGION"
echo "======================================================"

# ── ECS Cluster ───────────────────────────────────────────────────────────────
echo ""
echo "[1/4] 建立 ECS Cluster..."
aws ecs create-cluster \
  --cluster-name "$CLUSTER" \
  --capacity-providers FARGATE \
  --region "$REGION" > /dev/null 2>&1 || echo "  Cluster 已存在，跳過"
echo "  ECS Cluster 就緒：$CLUSTER"

# ── CloudWatch Log Groups ─────────────────────────────────────────────────────
echo ""
echo "[2/4] 建立 CloudWatch Log Groups..."
for log_group in "/ecs/scam-prediction-api" "/ecs/scam-prediction-streamlit"; do
  aws logs create-log-group --log-group-name "$log_group" --region "$REGION" > /dev/null 2>&1 \
    || echo "  Log group 已存在：$log_group"
  aws logs put-retention-policy \
    --log-group-name "$log_group" \
    --retention-in-days 30 \
    --region "$REGION" > /dev/null
  echo "  Log group 就緒（保留 30 天）：$log_group"
done

# ── Secrets Manager ───────────────────────────────────────────────────────────
echo ""
echo "[3/4] 建立 Secrets Manager 佔位符..."
echo "  請手動填入以下 secrets 的實際值："

secrets=(
  "scam-prediction/openai-api-key"
  "scam-prediction/postgres-password"
  "scam-prediction/api-key"
  "scam-prediction/api-gateway-url"
)

for secret in "${secrets[@]}"; do
  aws secretsmanager create-secret \
    --name "$secret" \
    --secret-string "PLACEHOLDER_REPLACE_ME" \
    --region "$REGION" > /dev/null 2>&1 \
    || echo "  Secret 已存在：$secret"
  echo "  Secret 就緒：$secret"
done

echo ""
echo "[4/4] IAM Roles 提醒..."
echo "  請確認以下 IAM Roles 已建立："
echo "  - ecsTaskExecutionRole（附加 AmazonECSTaskExecutionRolePolicy）"
echo "  - ecsTaskRole（附加 SecretsManagerReadWrite 或自訂最小權限）"

echo ""
echo "======================================================"
echo " 基礎設施建立完成！"
echo ""
echo " 下一步："
echo " 1. 更新 Secrets Manager 中的實際值："
echo "    aws secretsmanager update-secret --secret-id scam-prediction/openai-api-key \\"
echo "      --secret-string 'sk-your-key' --region $REGION"
echo ""
echo " 2. 建立 ECS Services（需要 VPC / Subnet / Security Group）："
echo "    參考 aws/ecs/service-config.md"
echo ""
echo " 3. 執行部署："
echo "    ./deploy.sh $ACCOUNT_ID $REGION"
echo "======================================================"
