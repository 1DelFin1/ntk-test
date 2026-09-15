from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal, Optional, Any, List, Dict, ClassVar


class ExtractedField(BaseModel):
    value: Optional[Any] = None
    status: Literal["present", "missing", "ambiguous"] = "missing"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: Optional[str] = None
    options: List[str] = Field(default_factory=list)

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v: Any) -> str:
        if isinstance(v, str):
            low = v.strip().lower()
            if low in ("present", "missing", "ambiguous"):
                return low
        return "missing"

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v: Any) -> float:
        try:
            return max(0.0, min(1.0, float(v)))
        except (TypeError, ValueError):
            return 0.0

    @field_validator("options", mode="before")
    @classmethod
    def ensure_list(cls, v: Any) -> List[str]:
        if v is None:
            return []
        if isinstance(v, list):
            return [str(item) for item in v]
        return []

    @field_validator("evidence", mode="before")
    @classmethod
    def str_or_none(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        return str(v)


class Extraction(BaseModel):
    company: ExtractedField = Field(default_factory=ExtractedField)
    origin_station: ExtractedField = Field(default_factory=ExtractedField)
    destination_station: ExtractedField = Field(default_factory=ExtractedField)
    cargo: ExtractedField = Field(default_factory=ExtractedField)

    wagons_count: ExtractedField = Field(default_factory=ExtractedField)
    tonnage: ExtractedField = Field(default_factory=ExtractedField)

    period_from: ExtractedField = Field(default_factory=ExtractedField)
    period_to: ExtractedField = Field(default_factory=ExtractedField)

    loading_conditions: ExtractedField = Field(default_factory=ExtractedField)
    unloading_conditions: ExtractedField = Field(default_factory=ExtractedField)

    rate: ExtractedField = Field(default_factory=ExtractedField)

    raw_summary: str = ""

    @field_validator("raw_summary", mode="before")
    @classmethod
    def ensure_summary(cls, v: Any) -> str:
        if v is None:
            return ""
        return str(v)

    model_config = {"extra": "ignore"}

    FIELD_NAMES: ClassVar[tuple] = (
        "company",
        "origin_station",
        "destination_station",
        "cargo",
        "wagons_count",
        "tonnage",
        "period_from",
        "period_to",
        "loading_conditions",
        "unloading_conditions",
        "rate",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        """Терпимость к вариациям LLM-выхода."""
        if isinstance(data, dict):
            for name in cls.FIELD_NAMES:
                val = data.get(name)
                if val is None:
                    data[name] = ExtractedField(status="missing").model_dump()
                elif isinstance(val, ExtractedField):
                    data[name] = val.model_dump()
                elif isinstance(val, dict):
                    pass
                else:
                    data[name] = ExtractedField(
                        value=val,
                        status="present",
                        confidence=1.0,
                    ).model_dump()
        return data
