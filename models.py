"""
models.py — Pydantic request/response models for Road Complaint Management System
"""

from pydantic import BaseModel
from typing import Optional
from enum import Enum


# ── Enum definitions (mirror MySQL ENUM columns) ──────────────────────────────

class DamageType(str, Enum):
    pothole      = "pothole"
    crack        = "crack"
    waterlogging = "waterlogging"
    subsidence   = "subsidence"


class Severity(str, Enum):
    low      = "low"
    medium   = "medium"
    critical = "critical"


class ComplaintStatus(str, Enum):
    open        = "open"
    in_progress = "in_progress"
    resolved    = "resolved"


class SkillType(str, Enum):
    road       = "road"
    drainage   = "drainage"
    electrical = "electrical"


class UserRole(str, Enum):
    citizen = "citizen"
    officer = "officer"
    admin   = "admin"


# ── Existing request bodies (kept for backward compatibility) ─────────────────

class CitizenCreate(BaseModel):
    """Body for POST /citizens — register a new citizen."""
    name:    str
    phone:   str
    email:   Optional[str] = None
    address: Optional[str] = None
    ward_no: Optional[int] = None


class ComplaintCreate(BaseModel):
    """JSON body kept for reference — actual POST /complaints uses Form()."""
    citizen_id:  int
    ward_id:     int
    description: str
    damage_type: DamageType
    severity:    Severity
    address:     str


class StatusUpdate(BaseModel):
    """Body for PATCH /complaints/{id}/status."""
    status:     ComplaintStatus
    changed_by: str


class WorkerAssign(BaseModel):
    """Body for PATCH /complaints/{id}/worker."""
    worker_id: int


# ── New models for Upgrade 1 (JWT Auth) ──────────────────────────────────────

class UserRegister(BaseModel):
    """Body for POST /register."""
    username: str
    password: str
    role:     UserRole = UserRole.citizen


class LoginResponse(BaseModel):
    """Response body for POST /login."""
    access_token: str
    token_type:   str
    role:         str
    username:     str
    user_id:      int
