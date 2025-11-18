from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class Email(Base):
    """
    Email model for storing sent emails
    """
    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    recipient_email = Column(String, nullable=False)
    sender_email = Column(String, nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="pending")  # pending, sent, failed
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    tenant = relationship("Tenant", back_populates="emails")

    def __repr__(self):
        return f"<Email(id={self.id}, recipient={self.recipient_email}, status={self.status})>"
