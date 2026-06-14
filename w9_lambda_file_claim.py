cat > w9_lambda_file_claim.py << 'EOF'
import json
import boto3
import uuid
from datetime import datetime

dynamodb = boto3.resource("dynamodb", region_name="us-east-2")
claims_table  = dynamodb.Table("w7-apex-claims")
policy_table  = dynamodb.Table("w7-apex-policies")

VALID_DAMAGE_TYPES = {"collision", "theft", "weather", "vandalism", "general"}

def handler(event, context):
    policy_id   = event.get("policy_id", "").strip().upper()
    description = event.get("description", "").strip()
    damage_type = event.get("damage_type", "general").strip().lower()

    if not policy_id:
        return {"statusCode": 400, "body": json.dumps({"error": "policy_id is required"})}
    if not description:
        return {"statusCode": 400, "body": json.dumps({"error": "description is required"})}
    if damage_type not in VALID_DAMAGE_TYPES:
        damage_type = "general"

    resp = policy_table.get_item(Key={"policy_id": policy_id})
    if not resp.get("Item"):
        return {"statusCode": 404, "body": json.dumps({"error": f"Policy {policy_id} not found"})}

    claim_id = f"CLM-{str(uuid.uuid4())[:8].upper()}"
    filed_at = datetime.utcnow().isoformat()

    claims_table.put_item(Item={
        "claim_id":    claim_id,
        "policy_id":   policy_id,
        "description": description,
        "damage_type": damage_type,
        "status":      "submitted",
        "filed_at":    filed_at,
    })

    return {"statusCode": 200, "body": json.dumps({
        "claim_id":  claim_id,
        "policy_id": policy_id,
        "status":    "submitted",
        "filed_at":  filed_at,
        "message":   f"Claim {claim_id} filed successfully. Our team will contact you within 2 business days."
    })}
EOF
