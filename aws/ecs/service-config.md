# ECS Service 建立指令

執行以下指令前，請先取得你的 VPC Subnet ID 和 Security Group ID：

```bash
# 查詢預設 VPC 的 Subnet
aws ec2 describe-subnets --filters "Name=default-for-az,Values=true" \
  --query "Subnets[*].SubnetId" --output text --region ap-northeast-1

# 查詢預設 Security Group
aws ec2 describe-security-groups --filters "Name=group-name,Values=default" \
  --query "SecurityGroups[*].GroupId" --output text --region ap-northeast-1
```

## 建立 API Service

```bash
aws ecs create-service \
  --cluster scam-prediction-cluster \
  --service-name scam-prediction-api-service \
  --task-definition scam-prediction-api \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[SUBNET_ID],
    securityGroups=[SG_ID],
    assignPublicIp=ENABLED
  }" \
  --region ap-northeast-1
```

## 建立 Streamlit Service

```bash
aws ecs create-service \
  --cluster scam-prediction-cluster \
  --service-name scam-prediction-streamlit-service \
  --task-definition scam-prediction-streamlit \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={
    subnets=[SUBNET_ID],
    securityGroups=[SG_ID],
    assignPublicIp=ENABLED
  }" \
  --region ap-northeast-1
```

## 查詢服務 Public IP

```bash
# 取得 Task ARN
TASK_ARN=$(aws ecs list-tasks --cluster scam-prediction-cluster \
  --service-name scam-prediction-api-service \
  --query "taskArns[0]" --output text --region ap-northeast-1)

# 取得 ENI ID
ENI_ID=$(aws ecs describe-tasks --cluster scam-prediction-cluster \
  --tasks $TASK_ARN --region ap-northeast-1 \
  --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" \
  --output text)

# 取得 Public IP
aws ec2 describe-network-interfaces \
  --network-interface-ids $ENI_ID \
  --query "NetworkInterfaces[0].Association.PublicIp" \
  --output text --region ap-northeast-1
```

## 存取端點

- API：`http://<PUBLIC_IP>:8000/docs`
- Streamlit：`http://<PUBLIC_IP>:8501`
