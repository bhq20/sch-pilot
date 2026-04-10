"""Modelos Pydantic v2 — entrada/saída da API."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class Segment(str, Enum):
    HUMANA = "HUMANA"
    VETERINARIA = "VETERINARIA"


class Role(str, Enum):
    ADMIN = "ADMIN"
    CONTROLLER = "CONTROLLER"
    VIEWER = "VIEWER"


class CCType(str, Enum):
    PRODUTIVO = "PRODUTIVO"
    AUXILIAR = "AUXILIAR"
    ADMINISTRATIVO = "ADMINISTRATIVO"


class CostNature(str, Enum):
    FIXO = "FIXO"
    VARIAVEL = "VARIAVEL"
    SEMI_VARIAVEL = "SEMI_VARIAVEL"


class CostCategory(str, Enum):
    PESSOAL = "PESSOAL"
    MATERIAL = "MATERIAL"
    MEDICAMENTO = "MEDICAMENTO"
    SERVICO = "SERVICO"
    INFRA = "INFRA"
    DEPRECIACAO = "DEPRECIACAO"
    OUTROS = "OUTROS"


# ----------------------------- Auth ---------------------------------
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: EmailStr
    full_name: str
    role: Role
    tenant_id: UUID
    tenant_name: str
    segment: Segment


# ----------------------------- Tenant -------------------------------
class TenantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    slug: str
    name: str
    segment: Segment
    active: bool
    created_at: datetime


# ------------------------- Cost Centers -----------------------------
class CostCenterIn(BaseModel):
    code: str = Field(..., max_length=30)
    name: str = Field(..., max_length=200)
    cc_type: CCType
    parent_id: Optional[UUID] = None


class CostCenterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    name: str
    cc_type: CCType
    parent_id: Optional[UUID] = None
    active: bool


# ------------------------- Accounts ---------------------------------
class AccountIn(BaseModel):
    code: str
    name: str
    category: CostCategory
    nature: CostNature


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    name: str
    category: CostCategory
    nature: CostNature
    active: bool


# ------------------------- Entries ----------------------------------
class EntryIn(BaseModel):
    cost_center_id: UUID
    account_id: UUID
    period: date
    amount: Decimal = Field(..., ge=0)
    notes: Optional[str] = None


class EntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    cost_center_id: UUID
    account_id: UUID
    period: date
    amount: Decimal
    source: str
    notes: Optional[str]


# ------------------------- Revenue ----------------------------------
class RevenueIn(BaseModel):
    cost_center_id: UUID
    period: date
    gross_revenue: Decimal = Field(..., ge=0)
    deductions: Decimal = Field(0, ge=0)
    variable_cost: Decimal = Field(0, ge=0)
    volume_units: int = 0


class RevenueOut(RevenueIn):
    model_config = ConfigDict(from_attributes=True)
    id: UUID


# ------------------------- Costing ----------------------------------
class CostingRequest(BaseModel):
    period: date
    method: str = Field(..., pattern="^(RKW|VARIAVEL)$")


class CostingRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    period: date
    method: str
    status: str
    summary: dict
    detail: dict
    created_at: datetime


# ------------------------- Dashboard --------------------------------
class DashboardKPIs(BaseModel):
    period: date
    total_revenue: Decimal
    total_cost: Decimal
    contribution_margin: Decimal
    margin_pct: float
    cost_center_count: int


class CostCenterSummary(BaseModel):
    cc_id: UUID
    cc_code: str
    cc_name: str
    cc_type: str
    total_cost: Decimal
    fixed_cost: Decimal
    variable_cost: Decimal


TokenResponse.model_rebuild()
