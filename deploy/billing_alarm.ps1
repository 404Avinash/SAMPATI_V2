# ─────────────────────────────────────────────────────────────────────────────
# SAMPATI AWS Billing Alarm Setup Script (PowerShell) ($15 Threshold)
#
# Configures an AWS CloudWatch metric alarm on EstimatedCharges with an SNS
# email subscription.
#
# Note: AWS Billing metrics are exclusively published in us-east-1 (N. Virginia).
#
# Usage:
#   powershell -File deploy\billing_alarm.ps1 -AlertEmail "your-email@domain.com"
# ─────────────────────────────────────────────────────────────────────────────

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$AlertEmail = "operator@example.com"
)

$ErrorActionPreference = "Stop"

$BillingRegion = "us-east-1"
$SnsTopicName  = "sampati-billing-alerts"
$AlarmName     = "sampati-billing-alarm-15usd"
$Threshold     = 15

Write-Host "=== SAMPATI AWS Billing Alarm Setup ===" -ForegroundColor Cyan
Write-Host "Billing Region : $BillingRegion (Required for AWS/Billing metrics)"
Write-Host "Alarm Threshold: `$$Threshold USD"
Write-Host "Target Email   : $AlertEmail"
Write-Host ""

# Validate email configuration
if ($AlertEmail -eq "operator@example.com" -or [string]::IsNullOrWhiteSpace($AlertEmail)) {
    Write-Host "======================================================================" -ForegroundColor Yellow
    Write-Host "[!] WARNING: Placeholder email detected ($AlertEmail)." -ForegroundColor Yellow
    Write-Host "    Please specify your recipient email before running:" -ForegroundColor Yellow
    Write-Host "      powershell -File deploy\billing_alarm.ps1 -AlertEmail your-email@domain.com" -ForegroundColor Yellow
    Write-Host "======================================================================" -ForegroundColor Yellow
    $InputEmail = Read-Host "Enter notification email address (or press Enter to abort)"
    if (-not [string]::IsNullOrWhiteSpace($InputEmail)) {
        $AlertEmail = $InputEmail
    } else {
        Write-Host "Aborted. No alarm created." -ForegroundColor Red
        exit 1
    }
}

# ── 1. Create SNS Topic ──────────────────────────────────────────────────────
Write-Host "Creating / locating SNS topic '$SnsTopicName' in $BillingRegion..."
$TopicArn = (aws sns create-topic `
    --name $SnsTopicName `
    --region $BillingRegion `
    --query "TopicArn" `
    --output text).Trim()

if (-not $TopicArn -or $TopicArn -eq "None") {
    throw "Failed to create or retrieve SNS Topic ARN."
}
Write-Host "  SNS Topic ARN: $TopicArn"

# ── 2. Subscribe Email to SNS Topic ──────────────────────────────────────────
Write-Host "Subscribing '$AlertEmail' to topic..."
$SubArn = (aws sns subscribe `
    --topic-arn $TopicArn `
    --protocol email `
    --notification-endpoint $AlertEmail `
    --region $BillingRegion `
    --query "SubscriptionArn" `
    --output text).Trim()

Write-Host "  Subscription status: $SubArn"
Write-Host "  [!] An AWS Notification - Subscription Confirmation email has been sent to $AlertEmail." -ForegroundColor Yellow
Write-Host "      You MUST click the confirmation link in the email to activate alerts." -ForegroundColor Yellow

# ── 3. Create CloudWatch Billing Alarm ────────────────────────────────────────
Write-Host "Creating CloudWatch billing alarm for EstimatedCharges > `$$Threshold USD..."
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

Write-Host ""
Write-Host "=== Billing Alarm Setup Complete ===" -ForegroundColor Green
Write-Host "Alarm Name : $AlarmName"
Write-Host "Metric     : AWS/Billing -> EstimatedCharges > `$$Threshold USD"
Write-Host "Action     : SNS Topic ($TopicArn) -> $AlertEmail"
Write-Host ""
Write-Host "Verify status in AWS Console: https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#alarmsV2:"
