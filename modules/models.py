from pydantic import BaseModel, Field
from typing import List, Optional


class CreatorContributor(BaseModel):
    name: str
    affiliation: Optional[str] = ""
    orcid: Optional[str] = ""
    type: Optional[str] = "person"
    role: Optional[str] = None


class DateMetadata(BaseModel):
    date: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    type: str
    description: Optional[str] = None


class Community(BaseModel):
    identifier: str


class Metadata(BaseModel):
    upload_type: str
    title: str
    description: str
    creators: List[CreatorContributor]
    contributors: List[CreatorContributor] = Field(default_factory=list)
    access_right: str
    license: str
    keywords: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    publication_date: Optional[str] = None
    dates: List[DateMetadata] = Field(default_factory=list)
    publisher: Optional[str] = None
    communities: List[Community] = Field(default_factory=list)
    language: Optional[str] = None
    doi: Optional[str] = None
    prereserve_doi: Optional[bool] = None