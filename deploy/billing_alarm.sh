#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# SAMPATI AWS Billing Alarm Setup Script ($15 Threshold)
#
# Configures an AWS CloudWatch metric alarm on EstimatedCharges with an SNS
# email subscription.
#
# Note: AWS Billing metrics are exclusively published in us-east-1 (N. Virginia).
#
# Usage:
#   1. Set your notification email in the ALERT_EMAIL variable below or pass it
#      as the first argument:
#        ./deploy/billing_alarm.sh admin@yourdomain.com
#      or
#        ALERT_EMAIL="admin@yourdomain.com" ./deploy/billing_alarm.sh
#   2. Check your inbox and confirm the AWS SNS Subscription confirmation email.
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── CONFIGURATION ────────────────────────────────────────────────────────────
# Set your alert recipient email here, or pass it via command-line argument / env var:
ALERT_EMAIL="${1:-${ALERT_EMAIL:-"operator@example.com"}}"

BILLING_REGION="us-east-1"
SNS_TOPIC_NAME="sampati-billing-alerts"
ALARM_NAME="sampati-billing-alarm-15usd"
THRESHOLD="15"

echo "=== SAMPATI AWS Billing Alarm Setup ==="
echo "Billing Region : $BILLING_REGION (Required for AWS/Billing metrics)"
echo "Alarm Threshold: \$$THRESHOLD USD"
echo "Target Email   : $ALERT_EMAIL"
echo ""

# Validate email configuration
if [ "$ALERT_EMAIL" = "operator@example.com" ] || [ -z "$ALERT_EMAIL" ]; then
    echo "======================================================================"
    echo "[!] WARNING: Placeholder email detected ($ALERT_EMAIL)."
    echo "    Please set a valid recipient email before running:"
    echo "      ./deploy/billing_alarm.sh your-email@domain.com"
    echo "    or update the ALERT_EMAIL variable in this script."
    echo "======================================================================"
    read -rp "Enter notification email address (or press Enter to abort): " INPUT_EMAIL
    if [ -n "$INPUT_EMAIL" ]; then
        ALERT_EMAIL="$INPUT_EMAIL"
    else
        echo "Aborted. No alarm created."
        exit 1
    fi
fi

# ── 1. Create SNS Topic ──────────────────────────────────────────────────────
echo "Creating / locating SNS topic '$SNS_TOPIC_NAME' in $BILLING_REGION..."
TOPIC_ARN=$(aws sns create-topic \
  --name "$SNS_TOPIC_NAME" \
  --region "$BILLING_REGION" \
  --query "TopicArn" \
  --output text)

if [ -z "$TOPIC_ARN" ] || [ "$TOPIC_ARN" = "None" ]; then
    echo "Error: Failed to create or retrieve SNS Topic ARN." >&2
    exit 1
fi

echo "  SNS Topic ARN: $TOPIC_ARN"

# ── 2. Subscribe Email to SNS Topic ──────────────────────────────────────────
echo "Subscribing '$ALERT_EMAIL' to topic..."
SUBSCRIPTION_ARN=$(aws sns subscribe \
  --topic-arn "$TOPIC_ARN" \
  --protocol email \
  --notification-endpoint "$ALERT_EMAIL" \
  --region "$BILLING_REGION" \
  --query "SubscriptionArn" \
  --output text)

echo "  Subscription status: $SUBSCRIPTION_ARN"
echo "  [!] An AWS Notification - Subscription Confirmation email has been sent to $ALERT_EMAIL."
echo "      You MUST click the confirmation link in the email to activate alerts."

# ── 3. Create CloudWatch Billing Alarm ────────────────────────────────────────
echo "Creating CloudWatch billing alarm for EstimatedCharges > \$$THRESHOLD USD..."
aws cloudwatch put-metric-alarm \
  --alarm-name "$ALARM_NAME" \
  --alarm-description "Trigger alarm when AWS monthly estimated charges exceed $THRESHOLD USD" \
  --metric-name "EstimatedCharges" \
  --namespace "AWS/Billing" \
  --statistic "Maximum" \
  --period 21600 \
  --threshold "$THRESHOLD" \
  --comparison-operator "GreaterThanThreshold" \
  --dimensions "Name=Currency,Value=USD" \
  --evaluation-periods 1 \
  --alarm-actions "$TOPIC_ARN" \
  --region "$BILLING_REGION"

echo ""
echo "=== Billing Alarm Setup Complete ==="
echo "Alarm Name : $ALARM_NAME"
echo "Metric     : AWS/Billing -> EstimatedCharges > \$$THRESHOLD USD"
echo "Action     : SNS Topic ($TOPIC_ARN) -> $ALERT_EMAIL"
echo ""
echo "Verify status in AWS Console: https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#alarmsV2:"
