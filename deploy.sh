#!/bin/bash
# ── AWS ECS 一鍵部署腳本 ──────────────────────────────────────────────────────
# 使用方式：
#   chmod +x deploy.sh
#   ./deploy.sh <AWS_ACCOUNT_ID> <AWS_REGION> [--push-only | --deploy-only]
#
# 前置需求：
#   - AWS CLI 已設定（aws configure）
#   - Docker 已安裝並執行中
#   - 已建立 ECR repositories（見下方說明）

set -e  # 任何指令失敗即中止

# ── 參數 ──────────────────────────────────────────────────────────────────────
ACCOUNT_ID="${1:?請提供 AWS Account ID，例如：./deploy.sh 123456789012 ap-northeast-1}"
REGION="${2:?請提供 AWS Region，例如：ap-northeast-1}"
MODE="${3:-all}"  # all | push-only | deploy-only

API_REPO="scam-prediction-api"
STREAMLIT_REPO="scam-prediction-streamlit"
API_IMAGE="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$API_REPO"
STREAMLIT_IMAGE="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$STREAMLIT_REPO"
ECS_CLUSTER="scam-prediction-cluster"

echo "======================================================"
echo " AI 詐騙進化預測系統 - AWS ECS 部署"
echo " Account: $ACCOUNT_ID | Region: $REGION"
echo "======================================================"

# ── Step 1：ECR 登入 ──────────────────────────────────────────────────────────
if [[ "$MODE" != "--deploy-only" ]]; then
  echo ""
  echo "[1/4] 登入 ECR..."
  aws ecr get-login-password --region "$REGION" \
    | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

  # 確保 ECR repositories 存在
  for repo in "$API_REPO" "$STREAMLIT_REPO"; do
    aws ecr describe-repositories --repository-names "$repo" --region "$REGION" > /dev/null 2>&1 || \
      aws ecr create-repository --repository-name "$repo" --region "$REGION" \
        --image-scanning-configuration scanOnPush=true > /dev/null
    echo "  ECR repository 就緒：$repo"
  done

  # ── Step 2：Build & Push ────────────────────────────────────────────────────
  echo ""
  echo "[2/4] 建置並推送 Docker images..."

  echo "  Building API image..."
  docker build -t "$API_IMAGE:latest" -f Dockerfile .
  docker push "$API_IMAGE:latest"
  echo "  API image 推送完成"

  echo "  Building Streamlit image..."
  docker build -t "$STREAMLIT_IMAGE:latest" -f Dockerfile.streamlit .
  docker push "$STREAMLIT_IMAGE:latest"
  echo "  Streamlit image 推送完成"
fi

# ── Step 3：更新 Task Definitions ─────────────────────────────────────────────
if [[ "$MODE" != "--push-only" ]]; then
  echo ""
  echo "[3/4] 更新 ECS Task Definitions..."

  # 替換 Task Definition 中的佔位符
  for file in aws/ecs/api-task-definition.json aws/ecs/streamlit-task-definition.json; do
    sed "s/ACCOUNT_ID/$ACCOUNT_ID/g; s/REGION/$REGION/g" "$file" > /tmp/$(basename "$file")
  done

  API_TASK_ARN=$(aws ecs register-task-definition \
    --cli-input-json file:///tmp/api-task-definition.json \
    --region "$REGION" \
    --query "taskDefinition.taskDefinitionArn" \
    --output text)
  echo "  API Task Definition: $API_TASK_ARN"

  STREAMLIT_TASK_ARN=$(aws ecs register-task-definition \
    --cli-input-json file:///tmp/streamlit-task-definition.json \
    --region "$REGION" \
    --query "taskDefinition.taskDefinitionArn" \
    --output text)
  echo "  Streamlit Task Definition: $STREAMLIT_TASK_ARN"

  # ── Step 4：更新 ECS Services ───────────────────────────────────────────────
  echo ""
  echo "[4/4] 更新 ECS Services..."

  for service in "scam-prediction-api-service" "scam-prediction-streamlit-service"; do
    # 確認 service 存在
    if aws ecs describe-services --cluster "$ECS_CLUSTER" --services "$service" \
        --region "$REGION" --query "services[0].status" --output text 2>/dev/null | grep -q "ACTIVE"; then
      aws ecs update-service \
        --cluster "$ECS_CLUSTER" \
        --service "$service" \
        --force-new-deployment \
        --region "$REGION" > /dev/null
      echo "  Service 更新中：$service"
    else
      echo "  Service 不存在，請先執行 aws/setup.sh 建立基礎設施：$service"
    fi
  done

  echo ""
  echo "======================================================"
  echo " 部署完成！"
  echo " 等待服務穩定（約 2-3 分鐘）..."
  echo " 查看狀態：aws ecs describe-services --cluster $ECS_CLUSTER --region $REGION"
  echo "======================================================"
fi
