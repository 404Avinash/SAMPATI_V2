#!/usr/bin/env python3
"""
Fox Guard - Synthetic SMS Dataset Generator
Generates multi-lingual (English, Hindi, Hinglish) SMS messages for
training a FastText intent classifier.

Labels:
  __label__fraud   - Phishing, fake alerts, UPI scam links
  __label__urgent  - Urgency-based manipulation (high risk)
  __label__otp     - Legitimate OTP messages (low risk)
  __label__promo   - Promotional / marketing messages
  __label__safe    - Benign, harmless messages

Usage:
  python generate_dataset.py
Output:
  sms_train.txt  (80% split)
  sms_test.txt   (20% split)
"""

import random
import os

random.seed(42)

# ─────────────────────────────────────────────
# Template pools
# ─────────────────────────────────────────────

BANKS    = ["SBI", "HDFC", "ICICI", "Axis", "PNB", "Kotak", "BOB", "Canara"]
AMOUNTS  = ["500", "1000", "2000", "5000", "10000", "25000", "50000"]
LINKS    = ["bit.ly/3xKy", "tinyurl.com/9z2", "t.co/aXz", "rb.gy/abc", "cutt.ly/xyz"]
OTPS     = [str(random.randint(100000, 999999)) for _ in range(200)]
SERVICES = ["PhonePe", "Google Pay", "Paytm", "BHIM", "Amazon Pay"]
ORDERS   = [f"ORD{random.randint(10000,99999)}" for _ in range(100)]

def pick(lst): return random.choice(lst)

# ─── FRAUD templates ──────────────────────────────────────────────────────────
FRAUD_TEMPLATES = [
    # English
    "Your {bank} account has been SUSPENDED. Complete KYC now or lose access: {link}",
    "ALERT: Unauthorized login on your {bank} account. Secure it: {link}",
    "Congratulations! You have won Rs {amount}. Claim your prize: {link}",
    "Income Tax Dept: Refund of Rs {amount} is pending. Verify now: {link}",
    "Your UPI ID is blocked. Update details immediately at {link}",
    "FINAL WARNING: Account closure in 24 hours. Click {link} to prevent",
    "Loan approved Rs {amount}. Submit documents at {link} before offer expires",
    "Rs {amount} deducted from your account. Dispute now: {link}",
    "Dear customer, your {service} wallet needs KYC. Update: {link}",
    "IRCTC: Your booking is cancelled. Get refund at {link}",
    "PM Kisan: Rs {amount} pending in your name. Verify Aadhaar: {link}",
    "Dear user your SIM card will be blocked in 2 hours. Verify: {link}",
    "You are selected for free insurance. Register now at {link}",
    "UIDAI: Your Aadhaar is deactivated. Reactivate at {link}",
    "Your credit card bill is overdue. Pay now to avoid penalty: {link}",
    # Hindi
    "Aapka {bank} account band ho jayega. KYC complete karein: {link}",
    "Aapke account se Rs {amount} debit hua. Agar aapne nahi kiya to {link}",
    "Aapko Rs {amount} ka inam mila hai. Abhi claim karein: {link}",
    "Aapki UPI ID band ho gayi. Turant update karein: {link}",
    "ALERT: Aapke account mein suspicious activity hai. Check karein: {link}",
    "Aapka Aadhaar verify nahi hai. Abhi karein warna band ho jayega: {link}",
    "Sarkar yojana: Aapke naam Rs {amount} pending hai. Link par click karein: {link}",
    # Hinglish
    "Bhai aapka account block ho gaya KYC nahi kiya isliye: {link}",
    "Urgent: Account mein problem hai, abhi click karo: {link}",
    "Lottery winner ho aap, Rs {amount} claim karo: {link}",
    "Aapka {bank} account suspend hogaya verify karo jaldi: {link}",
    "Paisa wapas lena hai to yahan click karo: {link}",
    "Account ki expiry aa rahi hai update karo: {link}",
]

# ─── URGENT templates ────────────────────────────────────────────────────────
URGENT_TEMPLATES = [
    # English
    "URGENT: Rs {amount} debited from your {bank} account. If not authorised call 1800-XXX",
    "IMPORTANT: Your {bank} account shows suspicious login. Call us immediately",
    "FINAL NOTICE: Your account will be permanently closed. Contact support now",
    "SBI FRAUD ALERT: Rs {amount} attempted from your account. Call 1800 to block",
    "Action Required: {service} payment of Rs {amount} failed. Retry immediately",
    "Your EMI of Rs {amount} is overdue. Pay now to avoid CIBIL impact",
    "NOTICE: Your PAN card is linked to a fraud case. Contact cybercrime: 1930",
    "Your phone number will be disconnected in 2 hours due to KYC non-compliance",
    # Hindi
    "TATKAL: Aapke account se Rs {amount} nikalne ki koshish ho rahi hai",
    "Aapka number 2 ghante mein band ho jayega. Abhi call karein helpline par",
    "Aapke naam par fraud case darj hua. Police se bachne ke liye call karein",
    # Hinglish
    "Bhai account mein fraud ho raha hai abhi call kar helpline pe",
    "Turant action lo warna account block ho jayega permanently",
    "Rs {amount} pending hai EMI ka, pay karo ya CIBIL kharab hoga",
]

# ─── OTP templates ───────────────────────────────────────────────────────────
OTP_TEMPLATES = [
    # English - These are SAFE
    "{bank}: Your OTP for login is {otp}. Valid for 10 minutes. Do NOT share.",
    "{service} OTP: {otp}. Use this to complete your transaction. Never share.",
    "Your {bank} transaction OTP is {otp}. Valid 5 min. Don't share with anyone.",
    "OTP for your {bank} NetBanking login: {otp}. Expires in 3 minutes.",
    "Use OTP {otp} to verify your {service} account. Valid for 10 min.",
    "{bank}: {otp} is your OTP for UPI registration. Do not share this OTP.",
    "HDFC Bank OTP {otp} for online purchase Rs {amount}. Valid 5 min.",
    "Your Aadhaar OTP is {otp}. Do not share this OTP with anyone.",
    "IRCTC OTP for booking: {otp}. Valid for 10 minutes. Keep it secret.",
    # Hindi
    "Aapka {bank} OTP hai {otp}. Kisi ko share na karein. 10 minute valid.",
    "{service} OTP: {otp}. Kisi ke saath share mat karna.",
    # Hinglish
    "{bank} ka OTP {otp} hai, valid 5 min, kisi ko mat batana",
]

# ─── PROMO templates ─────────────────────────────────────────────────────────
PROMO_TEMPLATES = [
    # English
    "Flat 50% OFF on all orders today! Shop now. Use code SAVE50",
    "{service} offer: Get Rs {amount} cashback on your next transaction",
    "Flipkart Big Sale: Upto 80% OFF on electronics. Shop now!",
    "Amazon Prime Day: Exclusive deals for members. Check app for offers",
    "Airtel: Recharge with Rs 299 and get unlimited data for 28 days",
    "Jio offer: Get 2GB/day data at just Rs 149. Recharge now!",
    "Swiggy: Order above Rs 299 and get Rs 50 off. Use SWIGGY50",
    "Zomato Gold special: Free delivery on all orders this weekend",
    "HDFC credit card exclusive: 10% cashback on Amazon for members",
    # Hindi
    "Aaj 50% chhoot mil rahi hai. Abhi order karein!",
    "{service} par cashback mil raha hai Rs {amount} ka. Use karein",
    # Hinglish
    "Kal tak offer hai, jaldi karo 50% off chal raha hai",
    "Aaj ka deal: {service} pe extra cashback, miss mat karo",
]

# ─── SAFE templates ──────────────────────────────────────────────────────────
SAFE_TEMPLATES = [
    # English
    "Your order {order} has been delivered. Thank you for shopping with us.",
    "{bank}: Your account balance is Rs {amount}. Last updated just now.",
    "Your flight PNR {order} is confirmed. Check-in opens 48 hours before.",
    "Welcome to {bank}! Your account is now active. Thank you.",
    "Your electricity bill of Rs {amount} has been paid successfully.",
    "{service}: Transaction of Rs {amount} successful. Ref: {order}",
    "Your appointment is confirmed for tomorrow at 10 AM.",
    "Airtel: Your recharge of Rs 299 was successful. Validity: 28 days.",
    "Your EMI of Rs {amount} for loan account has been debited. Ref: {order}",
    "IRCTC: Your e-ticket for train 12302 is confirmed. PNR: {order}",
    "Reminder: Your appointment is scheduled for tomorrow.",
    "Your subscription has been renewed successfully for another month.",
    # Hindi
    "Aapka order {order} deliver ho gaya. Dhanyawad!",
    "Aapke account mein Rs {amount} credit hua. {bank}",
    "Bijli ka bill Rs {amount} successfully bhar diya gaya.",
    # Hinglish
    "Bhai order aa gaya {order} wala",
    "Account mein paisa aa gaya Rs {amount}",
    "Recharge successful ho gaya, thanks!",
]

# ─────────────────────────────────────────────
# Rendering helper
# ─────────────────────────────────────────────

def render(template: str) -> str:
    return (template
            .replace("{bank}",    pick(BANKS))
            .replace("{amount}",  pick(AMOUNTS))
            .replace("{link}",    pick(LINKS))
            .replace("{otp}",     pick(OTPS))
            .replace("{service}", pick(SERVICES))
            .replace("{order}",   pick(ORDERS)))

# ─────────────────────────────────────────────
# Generate dataset
# ─────────────────────────────────────────────

def generate_examples(label: str, templates: list, count: int) -> list:
    examples = []
    for _ in range(count):
        template = pick(templates)
        text = render(template)
        # Lowercase and clean — FastText works on lowercase
        text = text.lower().strip()
        examples.append(f"{label} {text}")
    return examples

def main():
    all_examples = []

    # Generate more fraud/urgent since they are critical
    all_examples += generate_examples("__label__fraud",  FRAUD_TEMPLATES,  600)
    all_examples += generate_examples("__label__urgent", URGENT_TEMPLATES, 400)
    all_examples += generate_examples("__label__otp",    OTP_TEMPLATES,    500)
    all_examples += generate_examples("__label__promo",  PROMO_TEMPLATES,  400)
    all_examples += generate_examples("__label__safe",   SAFE_TEMPLATES,   500)

    random.shuffle(all_examples)

    total = len(all_examples)
    split = int(total * 0.8)
    train = all_examples[:split]
    test  = all_examples[split:]

    out_dir = os.path.dirname(os.path.abspath(__file__))
    train_path = os.path.join(out_dir, "sms_train.txt")
    test_path  = os.path.join(out_dir, "sms_test.txt")

    with open(train_path, "w", encoding="utf-8") as f:
        f.write("\n".join(train))

    with open(test_path, "w", encoding="utf-8") as f:
        f.write("\n".join(test))

    print(f"✅ Dataset generated!")
    print(f"   Total  : {total} examples")
    print(f"   Train  : {len(train)} -> {train_path}")
    print(f"   Test   : {len(test)}  -> {test_path}")
    print(f"\nLabel distribution:")
    from collections import Counter
    counts = Counter(e.split()[0] for e in all_examples)
    for lbl, cnt in sorted(counts.items()):
        print(f"   {lbl:<22} {cnt}")

if __name__ == "__main__":
    main()
