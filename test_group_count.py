import logging
from app.database import SessionLocal
from app.crud.group import get_groups
from app.schemas.group import GroupResponse

logging.basicConfig(level=logging.INFO)

db = SessionLocal()
try:
    groups = get_groups(db=db, limit=5)
    for g in groups:
        resp = GroupResponse.model_validate(g)
        print(f"Group: {resp.name_en}, Products Count: {resp.active_products_count}")
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
