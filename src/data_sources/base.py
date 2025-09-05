from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Type, List
import pandas as pd

@dataclass
class SourceResult:
    df: pd.DataFrame
    metadata: Dict[str, Any]

class DataSource(ABC):
    source_type: str
    def __init__(self, **kwargs):
        self.params = kwargs
    @abstractmethod
    def load(self) -> SourceResult:
        ...

_DATA_SOURCE_REGISTRY: Dict[str, Type[DataSource]] = {}

def register_source(cls: Type[DataSource]) -> Type[DataSource]:
    key = cls.source_type
    if key in _DATA_SOURCE_REGISTRY:
        raise ValueError(f"Duplicate data source key: {key}")
    _DATA_SOURCE_REGISTRY[key] = cls
    return cls

def available_sources() -> List[str]:
    return list(_DATA_SOURCE_REGISTRY.keys())

def build_source(source_type: str, **kwargs) -> DataSource:
    if source_type not in _DATA_SOURCE_REGISTRY:
        raise KeyError(f"Unknown data source: {source_type}")
    return _DATA_SOURCE_REGISTRY[source_type](**kwargs)