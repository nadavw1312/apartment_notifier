# 🧩 AI-Service-Layers.md

## Purpose

This document explains the architecture and responsibilities of each layer in our service structure.
It is designed for AI agents and developers to follow a consistent, scalable pattern when adding or maintaining services in this project.

Services are split into clear layers to enforce **separation of concerns**, **testability**, and **maintainability**.

> **Note:** Refer to existing services (e.g., `user` service) as practical examples of this structure.

---

## 📂 Folder & File Structure

Each service resides in:
```
src/services/<service_name>/
```

The typical files in a service are:
```
<service_name>_models.py       # Database models (SQLAlchemy)
<service_name>_dal.py          # Data Access Layer (DAL)
<service_name>_bl.py           # Business Logic Layer (BL)
<service_name>_api_schemas.py  # API request/response schemas
<service_name>_api.py          # API router (FastAPI)
```

---

## Layer Overview

### 1. Models Layer — _models.py

Defines the database schema for this service using **SQLAlchemy ORM**.

Responsibilities:
- Define table name and fields.
- Use correct data types and constraints.
- Inherit from common base classes (e.g., Base, TimestampMixin).

Guidelines:
- Keep strictly data-focused (no business logic).
- Default values, nullable options, and constraints must reflect real-world data accurately.
- Add docstrings for clarity.

Example:
```python
class ExampleModel(Base, TimestampMixin):
    __tablename__ = "examples"

    id: Mapped[INTPK]
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
```

---

### 2. Data Access Layer (DAL) — _dal.py

Handles **direct communication with the database**.

Responsibilities:
- Abstract raw SQL operations.
- Provide reusable methods: get_by_id, get_all, add, update, delete, etc.
- Always accept AsyncSession for database operations.
- Return raw model instances (no external logic).

Guidelines:
- Focus on efficiency and clarity.
- Avoid leaking database queries to other layers.
- All methods should be async.
- Use clear method names.

Strict Rule:
❌ **DAL layer must not call other DALs or BL layers.**

Example:
```python
class ExampleDAL:
    @classmethod
    async def get_by_id(cls, db: AsyncSession, example_id: int) -> Optional[ExampleModel]:
        result = await db.execute(select(ExampleModel).where(ExampleModel.id == example_id))
        return result.scalars().first()
```

---

### 3. Business Logic Layer (BL) — _bl.py

Implements **core business rules** and workflows.

Responsibilities:
- Process data from DAL.
- Apply validation and decision-making logic.
- Prepare data before sending it to DAL or API layers.
- Compose multiple DAL calls when needed.

Guidelines:
- Keep methods async.
- Avoid direct database queries (use DAL).
- Prefer classmethods for consistency.
- Ensure input parameters are validated.

Strict Rule:
✅ **BL layer may:**
- Use its own DAL
- Use other services' BL layers

❌ **BL layer must not call other services' DALs directly.**

Example:
```python
class ExampleBL:
    @classmethod
    async def create_example(cls, db: AsyncSession, name: str) -> ExampleModel:
        return await ExampleDAL.add(db, name=name)
```

---

### 4. API Schemas Layer — _api_schemas.py

Defines **input and output models** for APIs using **Pydantic**.

Responsibilities:
- Serialize and validate incoming requests.
- Format outgoing responses.
- Ensure API contracts are clear and documented.

Guidelines:
- Keep Pydantic models slim and descriptive.
- Use correct field types and defaults.
- Add Config classes with from_attributes = True for ORM compatibility.

Example:
```python
class ExampleCreateRequest(BaseModel):
    name: str

class ExampleResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
```

---

### 5. API Router Layer — _api.py

Defines **HTTP endpoints** for the service using **FastAPI**.

Responsibilities:
- Define routes and their methods (GET, POST, PUT, DELETE).
- Inject dependencies like database sessions.
- Call the BL layer for processing.
- Return API schemas as responses.

Guidelines:
- Use APIRouter.
- Annotate route functions properly.
- Avoid direct DAL access — always go through BL.
- Include meaningful route summaries and descriptions.

Example:
```python
router = APIRouter()

@router.post("/examples")
async def create_example(request: ExampleCreateRequest, db: AsyncSession = Depends(SQL_DB_MANAGER.session)):
    result = await ExampleBL.create_example(db=db, name=request.name)
    return ExampleResponse.from_orm(result)
```

---

## General Best Practices

- ✅ Use async/await everywhere.
- ✅ Follow layered structure strictly: API ➡️ BL ➡️ DAL ➡️ Models.
- ✅ Keep files clean and focused.
- ✅ Add docstrings for all public methods and classes.
- ✅ Consistent naming across layers.
- ✅ Use existing services as reference.

---

## Conclusion

By following this structure, our services stay clean, predictable, and scalable — whether developed by human engineers or AI agents.