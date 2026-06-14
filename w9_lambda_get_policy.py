cat > w9_lambda_get_policy.py << 'EOF'
import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
table = dynamodb.Table("w7-apex-policies")

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def handler(event, context):
    policy_id = event.get("policy_id", "").strip().upper()
    if not policy_id:
        return {"statusCode": 400, "body": json.dumps({"error": "policy_id is required"})}

    resp = table.get_item(Key={"policy_id": policy_id})
    item = resp.get("Item")
    if not item:
        return {"statusCode": 404, "body": json.dumps({"error": f"Policy {policy_id} not found"})}

    return {"statusCode": 200, "body": json.dumps(item, default=decimal_default)}
EOF