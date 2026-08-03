"""Seed initial platform tenant and tenant admin user for local development/testing."""

from __future__ import annotations

import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from core.security import hash_password
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository


def seed() -> None:
    settings = get_settings()
    engine = create_engine(settings.application_database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        tenant_repo = TenantRepository(session)
        user_repo = UserRepository(session)

        # 1. Seed default tenant
        tenant = tenant_repo.get_by_code("demo-tenant")
        if not tenant:
            tenant = tenant_repo.create(
                name="Demo Tenant",
                code="demo-tenant",
                settings={"environment": "development"},
            )
            print(f"Created Tenant: {tenant.name} ({tenant.code}) -> ID: {tenant.id}")
        else:
            print(f"Tenant already exists: {tenant.name} ({tenant.code}) -> ID: {tenant.id}")

        # 2. Seed default tenant admin user
        user = user_repo.get_by_tenant_and_email(tenant.id, "admin@demo.com")
        if not user:
            pwd_hash = hash_password("Admin123456!")
            user = user_repo.create(
                tenant_id=tenant.id,
                email="admin@demo.com",
                password_hash=pwd_hash,
                full_name="Tenant Admin",
                is_tenant_admin=True,
            )
            session.commit()
            print(f"Created Admin User: {user.email} -> ID: {user.id}")
        else:
            print(f"Admin User already exists: {user.email} -> ID: {user.id}")

    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}", file=sys.stderr)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
