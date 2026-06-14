cat > w9_lambda_get_quote.py << 'EOF'
import json
import boto3
import uuid
from decimal import Decimal

dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
table = dynamodb.Table("w7-apex-policies")

BASE_RATES = {"liability": 800, "collision": 1100, "comprehensive": 1400}

def handler(event, context):
    vehicle       = event.get("vehicle", "").strip()
    coverage      = event.get("coverage", "liability").lower().strip()
    driver_age    = event.get("driver_age", 30)
    customer_name = event.get("customer_name", "Prospective Customer").strip()

    if not vehicle:
        return {"statusCode": 400, "body": json.dumps({"error": "vehicle is required"})}

    try:
        driver_age = int(driver_age)
    except (ValueError, TypeError):
        driver_age = 30

    if coverage not in BASE_RATES:
        coverage = "liability"

    base = BASE_RATES[coverage]
    if driver_age < 25:
        base = int(base * 1.30)
    elif driver_age > 65:
        base = int(base * 1.15)

    deductible  = 500
    monthly     = round(base / 12, 2)
    quote_id    = f"QTE-{str(uuid.uuid4())[:8].upper()}"
    expiry_date = "2027-06-13"

    table.put_item(Item={
        "policy_id":     quote_id,
        "customer_name": customer_name,
        "vehicle":       vehicle,
        "coverage":      coverage,
        "premium":       Decimal(str(base)),
        "deductible":    Decimal(str(deductible)),
        "status":        "quote",
        "expiry":        expiry_date,
    })

    return {"statusCode": 200, "body": json.dumps({
        "quote_id":        quote_id,
        "vehicle":         vehicle,
        "coverage":        coverage,
        "annual_premium":  base,
        "monthly_premium": monthly,
        "deductible":      deductible,
        "valid_until":     expiry_date,
        "message": f"Quote {quote_id}: {coverage.title()} coverage for {vehicle} — ${base}/year (${monthly}/month) with ${deductible} deductible."
    })}
EOF