#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# SAMPATI AWS Deployment Script
# Uses: EC2 t3.micro (Free Tier) + Docker + nginx
# Cost: ~$0/month on free tier, ~$8/month after 12 months
#
# Prerequisites:
#   - AWS CLI installed and configured (aws configure)
#   - A key pair created in your region (update KEY_NAME below)
#   - Docker Hub account (optional — can also build on EC2)
#
# Usage:
#   chmod +x deploy/aws_deploy.sh
#   ./deploy/aws_deploy.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e

# ── CONFIG — edit these ──────────────────────────────────────────────────────
AWS_REGION="ap-south-1"       # Mumbai (closest to India)
KEY_NAME="sampati-key"        # Name of your EC2 key pair
INSTANCE_TYPE="t3.micro"      # Free tier eligible
AMI_ID="ami-0f58b397bc5c1f2e2" # Amazon Linux 2023 (Mumbai) — update if expired
SECURITY_GROUP="sampati-sg"
INSTANCE_NAME="sampati-upi"

echo "=== SAMPATI AWS Deployment ==="

# ── 1. Create Security Group ─────────────────────────────────────────────────
echo "Creating security group..."
SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=$SECURITY_GROUP" \
  --query "SecurityGroups[0].GroupId" \
  --output text --region $AWS_REGION 2>/dev/null)

if [ "$SG_ID" = "None" ] || [ -z "$SG_ID" ]; then
  SG_ID=$(aws ec2 create-security-group \
    --group-name $SECURITY_GROUP \
    --description "SAMPATI UPI Gateway" \
    --region $AWS_REGION \
    --query GroupId --output text)
  
  # Allow SSH, HTTP, HTTPS, and app port
  aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID --region $AWS_REGION \
    --ip-permissions \
    "IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=0.0.0.0/0}]" \
    "IpProtocol=tcp,FromPort=80,ToPort=80,IpRanges=[{CidrIp=0.0.0.0/0}]" \
    "IpProtocol=tcp,FromPort=443,ToPort=443,IpRanges=[{CidrIp=0.0.0.0/0}]" \
    "IpProtocol=tcp,FromPort=8000,ToPort=8000,IpRanges=[{CidrIp=0.0.0.0/0}]"
  
  echo "Security group created: $SG_ID"
else
  echo "Using existing security group: $SG_ID"
fi

# ── 2. Launch EC2 Instance ───────────────────────────────────────────────────
echo "Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type $INSTANCE_TYPE \
  --key-name $KEY_NAME \
  --security-group-ids $SG_ID \
  --region $AWS_REGION \
  --user-data file://deploy/ec2_userdata.sh \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
  --query "Instances[0].InstanceId" \
  --output text)

echo "Instance launched: $INSTANCE_ID"
echo "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $AWS_REGION

# ── 3. Get Public IP ─────────────────────────────────────────────────────────
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --region $AWS_REGION \
  --query "Reservations[0].Instances[0].PublicIpAddress" \
  --output text)

echo ""
echo "=== Deployment Complete ==="
echo "Instance ID : $INSTANCE_ID"
echo "Public IP   : $PUBLIC_IP"
echo ""
echo "Wait ~3-5 minutes for user-data script to finish, then:"
echo "  App URL  : http://$PUBLIC_IP"
echo "  API Docs : http://$PUBLIC_IP/docs"
echo "  SSH      : ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP"
echo ""
echo "To check startup logs:"
echo "  ssh -i ~/.ssh/$KEY_NAME.pem ec2-user@$PUBLIC_IP 'sudo journalctl -u sampati -f'"
