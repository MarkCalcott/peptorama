import re

from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator

DISALLOWED_TEXT = r'[#$%&@!?{}\\|~`"\'<>^,]'
DISALLOWED_SMILES = r'[^A-Za-z0-9#=\-\(\)\[\]\.@\/\\%\*+~:]'

class MonomerEntry(BaseModel):
    code: str
    name: str
    stereochemistry: str | None = Field(None, pattern="^(L|D|flat)$")
    base: str
    exact: str
    category: str | None = None
    smiles: str

    @field_validator("code", "name", "base", "exact", "category")
    @classmethod
    def no_disallowed_chars(cls, v):
        if v is None:
            return v
        if re.search(DISALLOWED_TEXT, v):
            raise ValueError(f"Contains invalid characters: {v}")
        return v

    @field_validator("smiles")
    @classmethod
    def valid_smiles_chars(cls, v):
        if v is None:
            return v
        if re.search(DISALLOWED_SMILES, v):
            raise ValueError(f"Contains invalid SMILES characters: {v}")
        return v

    @field_validator("base")
    @classmethod
    def no_dash_in_base(cls, v):
        if v and "-" in v:
            raise ValueError("Base field cannot contain dashes")
        return v

class PeptideInput(BaseModel):
    known: str = Field("", max_length=1_000_000)
    predicted: str = Field("", max_length=1_000_000)
    monomers: dict | None = None  # Optional user-uploaded monomer dictionary

    @model_validator(mode="after")
    def at_least_one(self):
        if not self.known.strip() and not self.predicted.strip():
            raise ValueError("Provide known peptides, predicted peptides, or both.")
        return self
 
    @field_validator("monomers")
    @classmethod
    def validate_dict_size(cls, v):
        if v and len(v) > 1000:
            raise ValueError("Monomer dictionary too large (max 1000 entries)")
        return v

# Settings for edges
class MonomerConfig(BaseModel):
    match: list[Literal["base", "exact"]] = Field(..., min_length=1)
    stereochemistry: list[Literal["relaxed", "moderate", "strict"]] = Field(
        ..., min_length=1
    )
    cutoff: float = Field(..., ge=0.0, le=100.0)

class TanimotoConfig(BaseModel):
    radius: list[int] = Field(..., min_length=1)
    cutoff: float = Field(..., ge=0.0, le=1.0)

class EdgeConfig(BaseModel):
    methods: list[Literal["monomer", "tanimoto"]] = Field(..., min_length=1)
    monomer: MonomerConfig
    tanimoto: TanimotoConfig

# Settings for filtering 
class FilterMonomerConfig(BaseModel):
    cutoff: float = Field(..., ge=0.0, le=100.0)
 
class FilterTanimotoConfig(BaseModel):
    cutoff: float = Field(..., ge=0.0, le=1.0)
 
class FilteringConfig(BaseModel): 
    filter: bool
    monomer: FilterMonomerConfig
    tanimoto: FilterTanimotoConfig

# Submit
class SubmitConfig(BaseModel):
    edge: EdgeConfig
    filtering: FilteringConfig

class SubmitRequest(BaseModel):
    input: PeptideInput
    config: SubmitConfig