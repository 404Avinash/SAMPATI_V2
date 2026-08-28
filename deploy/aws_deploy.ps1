# ─────────────────────────────────────────────────────────────────────────────
# SAMPATI AWS Deployment Script (PowerShell)
# Uses: EC2 t3.micro (Free Tier) + Docker + nginx
# Cost: ~$0/month on free tier, ~$8/month after 12 months
#
# Prerequisites:
#   - AWS CLI installed and configured (aws configure) with an IAM user
#     (NOT root credentials) scoped to AmazonEC2FullAccess
#   - A key pair created in your region (update $KeyName below)
#
# Usage:
#   powershell -File deploy\aws_deploy.ps1
# ─────────────────────────────────────────────────────────────────────────────

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$AlertEmail = "operator@example.com"
)

$ErrorActionPreference = "Stop"

# ── CONFIG — edit these ──────────────────────────────────────────────────────
$AwsRegion      = "ap-south-1"        # Mumbai (closest to India)
$KeyName        = "sampati-key"       # Name of your EC2 key pair (no .pem suffix)
$InstanceType   = "t3.micro"          # Free tier eligible
$SecurityGroup  = "sampati-sg"
$InstanceName   = "sampati-upi"

Write-Host "=== SAMPATI AWS Deployment ===" -ForegroundColor Cyan


# ── 0. Resolve latest Amazon Linux 2023 AMI for the region ──────────────────
Write-Host "Resolving latest Amazon Linux 2023 AMI..."
$AmiId = aws ssm get-parameters `
  --names "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64" `
  --region $AwsRegion `
  --query "Parameters[0].Value" --output text

if (-not $AmiId -or $AmiId -eq "None") {
    throw "Could not resolve AMI ID. Check your AWS region/credentials."
}
Write-Host "  AMI: $AmiId"

# ── 1. Create Security Group (idempotent) ───────────────────────────────────
Write-Host "Creating/locating security group..."
$SgId = aws ec2 describe-security-groups `
  --filters "Name=group-name,Values=$SecurityGroup" `
  --region $AwsRegion `
  --query "SecurityGroups[0].GroupId" --output text 2>$null

if (-not $SgId -or $SgId -eq "None") {
    $SgId = aws ec2 create-security-group `
      --group-name $SecurityGroup `
      --description "SAMPATI UPI Gateway" `
      --region $AwsRegion `
      --query "GroupId" --output text

    aws ec2 authorize-security-group-ingress --group-id $SgId --region $AwsRegion `
      --ip-permissions `
      "IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges=[{CidrIp=0.0.0.0/0}]" `
      "IpProtocol=tcp,FromPort=80,ToPort=80,IpRanges=[{CidrIp=0.0.0.0/0}]" `
      "IpProtocol=tcp,FromPort=443,ToPort=443,IpRanges=[{CidrIp=0.0.0.0/0}]" `
      "IpProtocol=tcp,FromPort=8000,ToPort=8000,IpRanges=[{CidrIp=0.0.0.0/0}]" | Out-Null

    Write-Host "  Security group created: $SgId"
} else {
    Write-Host "  Using existing security group: $SgId"
}

# ── 2. Launch EC2 Instance ───────────────────────────────────────────────────
Write-Host "Launching EC2 instance..."
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$userDataPath = Join-Path $scriptDir "ec2_userdata.sh"

$InstanceId = aws ec2 run-instances `
  --image-id $AmiId `
  --instance-type $InstanceType `
  --key-name $KeyName `
  --security-group-ids $SgId `
  --region $AwsRegion `
  --user-data "file://$userDataPath" `
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$InstanceName}]" `
  --query "Instances[0].InstanceId" --output text

Write-Host "  Instance launched: $InstanceId"
Write-Host "Waiting for instance to enter 'running' state..."
aws ec2 wait instance-running --instance-ids $InstanceId --region $AwsRegion

# ── 3. Get Public IP ─────────────────────────────────────────────────────────
$PublicIp = aws ec2 describe-instances `
  --instance-ids $InstanceId `
  --region $AwsRegion `
  --query "Reservations[0].Instances[0].PublicIpAddress" --output text

# ── 4. Set up CloudWatch Billing Alarm ($15 Threshold) ──────────────────────
Write-Host ""
Write-Host "Setting up AWS CloudWatch Billing Alarm ($15 threshold)..."
$BillingRegion = "us-east-1"
$SnsTopicName  = "sampati-billing-alerts"
$AlarmName     = "sampati-billing-alarm-15usd"
$Threshold     = 15

if ($AlertEmail -ne "operator@example.com" -and (-not [string]::IsNullOrWhiteSpace($AlertEmail))) {
    $TopicArn = (aws sns create-topic `
        --name $SnsTopicName `
        --region $BillingRegion `
        --query "TopicArn" `
        --output text).Trim()

    if (-not $TopicArn -or $TopicArn -eq "None") {
        throw "Failed to create or retrieve SNS Topic ARN."
    }

    aws sns subscribe `
        --topic-arn $TopicArn `
        --protocol email `
        --notification-endpoint $AlertEmail `
        --region $BillingRegion | Out-Null

    aws cloudwatch put-metric-alarm `
        --alarm-name $AlarmName `
        --alarm-description "Trigger alarm when AWS monthly estimated charges exceed $Threshold USD" `
        --metric-name "EstimatedCharges" `
        --namespace "AWS/Billing" `
        --statistic "Maximum" `
        --period 21600 `
        --threshold $Threshold `
        --comparison-operator "GreaterThanThreshold" `
        --dimensions "Name=Currency,Value=USD" `
        --evaluation-periods 1 `
        --alarm-actions $TopicArn `
        --region $BillingRegion

    Write-Host "  Billing alarm created for EstimatedCharges > `$$Threshold USD ($AlertEmail)" -ForegroundColor Green
    Write-Host "  [!] Please confirm the subscription email sent by AWS SNS to $AlertEmail." -ForegroundColor Yellow
} else {
    Write-Host "  [INFO] Default AlertEmail detected. To configure the `$15 billing alarm, run:" -ForegroundColor Yellow
    Write-Host "         powershell -File deploy\billing_alarm.ps1 -AlertEmail your-email@domain.com" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host "Instance ID : $InstanceId"
Write-Host "Public IP   : $PublicIp"
Write-Host ""
Write-Host "Wait ~3-5 minutes for the boot script to finish, then visit:"
Write-Host "  App URL  : http://$PublicIp"
Write-Host "  API Docs : http://$PublicIp/docs"
Write-Host ""
Write-Host "SSH (if you have an OpenSSH client / WSL / PuTTY):"
Write-Host "  ssh -i path\to\$KeyName.pem ec2-user@$PublicIp"
Write-Host ""
Write-Host "To verify reboot resilience:"
Write-Host "  ssh -i path\to\$KeyName.pem ec2-user@$PublicIp '/opt/sampati/deploy/verify_reboot.sh'"

