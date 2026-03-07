"""
Seed a partner lab and generate an API key for Lab API.
Run from project root: python -m scripts.seed_lab
"""
import asyncio
import hashlib
import secrets
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from visiondx.database.connection import AsyncSessionLocal, create_tables
from visiondx.database.models import Lab


def generate_lab_api_key() -> tuple[str, str]:
    """Returns (raw_key, key_hash). Store raw_key securely; only hash is stored in DB."""
    raw = "vdx_lab_" + secrets.token_urlsafe(24)
    key_hash = hashlib.sha256(raw.encode()).hexdigest()
    return raw, key_hash


async def seed_lab():
    await create_tables()
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Lab).where(Lab.slug == "demo-lab").limit(1))
        existing = result.scalar_one_or_none()
        if existing:
            print("Demo lab already exists. To reset, delete the lab and run again.")
            return
        raw_key, key_hash = generate_lab_api_key()
        lab = Lab(
            name="Demo Partner Lab",
            slug="demo-lab",
            api_key_hash=key_hash,
            address="123 Medical Ave",
            phone="555-0100",
            supports_home_collection=True,
        )
        db.add(lab)
        await db.commit()
        print("Lab created successfully.")
        print("Lab ID:", lab.id)
        print("Lab API Key (use in X-Lab-API-Key header):", raw_key)
        print("Save this key; it cannot be retrieved again.")


if __name__ == "__main__":
    asyncio.run(seed_lab())
