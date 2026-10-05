"""
SQLAlchemy ORM models for BioAge-X API database.
Tracks datasets, analyses, trained models, and experiment runs.
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from apps.api.core.database import Base


class DatasetRecord(Base):
    __tablename__ = "datasets"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    format = Column(String(20), nullable=False)
    n_samples = Column(Integer, default=0)
    n_features = Column(Integer, default=0)
    orientation = Column(String(50), default="samples_by_features")
    missing_fraction = Column(Float, default=0.0)
    age_column = Column(String(100), nullable=True)
    detected_modality = Column(String(50), default="unknown")
    profile_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    analyses = relationship("AnalysisRecord", back_populates="dataset", cascade="all, delete-orphan")
    models = relationship("ModelRecord", back_populates="dataset", cascade="all, delete-orphan")


class AnalysisRecord(Base):
    __tablename__ = "analyses"

    id = Column(String(50), primary_key=True, index=True)
    dataset_id = Column(String(50), ForeignKey("datasets.id"), nullable=False)
    status = Column(String(30), default="COMPLETED")
    modality = Column(String(50), default="methylation")
    preprocessed_path = Column(String(500), nullable=True)
    provenance_json = Column(Text, nullable=True)
    selected_features_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("DatasetRecord", back_populates="analyses")


class ModelRecord(Base):
    __tablename__ = "models"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    model_type = Column(String(50), nullable=False)  # ElasticNet, RandomForest, XGBoost, Fusion
    dataset_id = Column(String(50), ForeignKey("datasets.id"), nullable=False)
    mae = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    r2 = Column(Float, nullable=True)
    pearson_r = Column(Float, nullable=True)
    spearman_rho = Column(Float, nullable=True)
    n_features = Column(Integer, default=0)
    training_time_sec = Column(Float, default=0.0)
    artifact_path = Column(String(500), nullable=True)
    feature_importance_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("DatasetRecord", back_populates="models")


class ExperimentRecord(Base):
    __tablename__ = "experiments"

    id = Column(String(50), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    dataset_id = Column(String(50), nullable=False)
    model_id = Column(String(50), nullable=False)
    model_type = Column(String(50), nullable=False)
    metrics_json = Column(Text, nullable=True)
    acceleration_summary_json = Column(Text, nullable=True)
    report_json = Column(Text, nullable=True)
    pdf_path = Column(String(500), nullable=True)
    reproducibility_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
