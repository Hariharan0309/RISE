"""
User store for RISE login/register.
Persists registered users in a local JSON file and, when AWS is configured,
in DynamoDB (RISE-UserProfiles) so numbers are stored and work across instances.
"""
import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Directory for data (set RISE_DATA_DIR for Docker; default ./data)
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.getenv("RISE_DATA_DIR", os.path.join(_BASE, "data"))
USERS_FILE = os.path.join(DATA_DIR, "users.json")

# User ID format used by app and other tools (e.g. buying_group_tools, weather_alert_tools)
def _user_id_from_phone(phone: str) -> str:
    return f"farmer_{phone}"


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _get_dynamodb_table():
    """Return DynamoDB UserProfiles table if AWS is configured; else None."""
    try:
        from config import Config
        import boto3
        if not getattr(Config, "AWS_REGION", None):
            return None
        table_name = getattr(Config, "DYNAMODB_USER_PROFILES_TABLE", "RISE-UserProfiles")
        dynamodb = boto3.resource("dynamodb", region_name=Config.AWS_REGION)
        return dynamodb.Table(table_name)
    except Exception as e:
        logger.debug("DynamoDB user store not available: %s", e)
        return None


def _load_users() -> Dict[str, Dict[str, Any]]:
    """Load users from JSON file. Key = phone (normalized 10 digits)."""
    _ensure_dir()
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Could not load users file: %s", e)
        return {}


def _save_users(users: Dict[str, Dict[str, Any]]) -> None:
    _ensure_dir()
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error("Could not save users file: %s", e)
        raise


def _normalize_phone(phone: str) -> str:
    return "".join(c for c in str(phone).strip() if c.isdigit())[-10:] if phone else ""


def _user_to_dynamodb_item(user: Dict[str, Any]) -> Dict[str, Any]:
    """Convert our user dict to DynamoDB item (user_id, phone_number, etc.)."""
    phone = user["phone"]
    return {
        "user_id": _user_id_from_phone(phone),
        "phone_number": phone,
        "name": user["name"],
        "location": user.get("location", "Not specified"),
        "crops": user.get("crops", []),
    }


def _dynamodb_item_to_user(item: Dict[str, Any]) -> Dict[str, Any]:
    """Convert DynamoDB item to our user dict (phone, name, location, crops)."""
    return {
        "phone": item.get("phone_number", ""),
        "name": item.get("name", ""),
        "location": item.get("location", "Not specified"),
        "crops": item.get("crops", []),
    }


def register(phone: str, name: str, location: str = "", crops: list = None) -> Dict[str, Any]:
    """
    Register a new user or update existing.
    Saves to local file (always) and to DynamoDB when AWS is configured.
    Returns user record.
    """
    phone = _normalize_phone(phone)
    if len(phone) != 10:
        return {"success": False, "error": "Phone must be 10 digits"}
    if not (name or "").strip():
        return {"success": False, "error": "Name is required"}
    user = {
        "phone": phone,
        "name": (name or "").strip(),
        "location": (location or "").strip() or "Not specified",
        "crops": list(crops) if crops else [],
    }
    # Always persist to local file (e.g. local dev, or backup)
    users = _load_users()
    users[phone] = user
    _save_users(users)
    # Also store in DynamoDB when available (production persistence)
    table = _get_dynamodb_table()
    if table:
        try:
            table.put_item(Item=_user_to_dynamodb_item(user))
            logger.info("Registered user %s in DynamoDB", phone)
        except Exception as e:
            logger.warning("Could not save user to DynamoDB: %s", e)
    return {"success": True, "user": user}


def login(phone: str) -> Optional[Dict[str, Any]]:
    """
    Look up user by phone. Tries DynamoDB first (PhoneIndex), then local file.
    Returns user dict if found, else None.
    """
    phone = _normalize_phone(phone)
    if len(phone) != 10:
        return None
    # Prefer DynamoDB when available (source of truth in production)
    table = _get_dynamodb_table()
    if table:
        try:
            from boto3.dynamodb.conditions import Key
            resp = table.query(
                IndexName="PhoneIndex",
                KeyConditionExpression=Key("phone_number").eq(phone),
            )
            items = resp.get("Items", [])
            if items:
                return _dynamodb_item_to_user(items[0])
        except Exception as e:
            logger.debug("DynamoDB login lookup failed: %s", e)
    # Fallback to local file
    users = _load_users()
    return users.get(phone)
