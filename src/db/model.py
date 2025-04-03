from typing import Annotated
from sqlalchemy.orm import declarative_base, mapped_column

STR50 = Annotated[str, 50]
INTPK = Annotated[int, mapped_column(primary_key=True)]
Base = declarative_base()
