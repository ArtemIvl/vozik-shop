from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
from config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)

# sessionmaker with class_=AsyncSession is the same as async_sessionmaker
SessionLocal = sessionmaker( 
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session