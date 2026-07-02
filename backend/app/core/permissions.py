from typing import List, Dict

# Role hierarchy
# Higher roles include permissions of lower roles in standard checks, 
# but for simplicity, we map explicit permissions or define a level-based comparison.

ROLE_LEVELS: Dict[str, int] = {
    "super_admin": 100,
    "agency_admin": 80,
    "client_admin": 60,
    "marketing_manager": 40,
    "customer_support": 30,
    "branch_manager": 20,
    "read_only": 10
}

def has_role_permission(user_role: str, required_role: str) -> bool:
    user_level = ROLE_LEVELS.get(user_role, 0)
    required_level = ROLE_LEVELS.get(required_role, 0)
    return user_level >= required_level

def is_super_admin(role: str) -> bool:
    return role == "super_admin"

def is_agency_level(role: str) -> bool:
    return role in ["super_admin", "agency_admin"]

def is_client_level(role: str) -> bool:
    return role in ["super_admin", "agency_admin", "client_admin", "marketing_manager"]
