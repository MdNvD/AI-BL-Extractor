from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentInfo(BaseModel):
    bill_of_lading_number: Optional[str] = None
    booking_number: Optional[str] = None
    bl_type: Optional[str] = None
    issue_date: Optional[str] = None


class CarrierInfo(BaseModel):
    name: Optional[str] = None


class VesselInfo(BaseModel):
    name: Optional[str] = None
    voyage: Optional[str] = None


class PartiesInfo(BaseModel):
    shipper: Optional[str] = None
    consignee: Optional[str] = None
    notify_party: Optional[str] = None


class RouteInfo(BaseModel):
    place_of_receipt: Optional[str] = None
    port_of_loading: Optional[str] = None
    port_of_discharge: Optional[str] = None
    place_of_delivery: Optional[str] = None


class CargoInfo(BaseModel):
    description: Optional[str] = None
    package_count: Optional[int] = None
    gross_weight_kg: Optional[float] = None
    measurement_cbm: Optional[float] = None
    hs_code: Optional[str] = None


class ContainerInfo(BaseModel):
    container_number: Optional[str] = None
    seal_number: Optional[str] = None
    size: Optional[str] = None
    cartons: Optional[int] = None
    weight_kg: Optional[float] = None
    cbm: Optional[float] = None


class SummaryInfo(BaseModel):
    total_containers: Optional[int] = None
    total_cartons: Optional[int] = None
    total_weight_kg: Optional[float] = None
    total_cbm: Optional[float] = None


class BLExtraction(BaseModel):
    document: DocumentInfo = Field(default_factory=DocumentInfo)
    carrier: CarrierInfo = Field(default_factory=CarrierInfo)
    vessel: VesselInfo = Field(default_factory=VesselInfo)
    parties: PartiesInfo = Field(default_factory=PartiesInfo)
    route: RouteInfo = Field(default_factory=RouteInfo)
    cargo: CargoInfo = Field(default_factory=CargoInfo)
    containers: List[ContainerInfo] = Field(default_factory=list)
    freight: Optional[str] = None
    summary: SummaryInfo = Field(default_factory=SummaryInfo)