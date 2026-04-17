from sqlalchemy import create_engine as _create_engine, inspect


class DatabaseRepository:
    """資料表中繼資料查詢層。"""

    def list_main_table_names(self, engine):
        return inspect(engine).get_table_names()

    def list_fakedata_table_names(self, fakedata_db_path):
        fakedata_engine = _create_engine(f"sqlite:///{fakedata_db_path}", echo=False)
        return inspect(fakedata_engine).get_table_names()

    def get_columns(self, inspector, table_name, exclude=None):
        exclude = set(exclude or [])
        columns_info = inspector.get_columns(table_name)
        return [col["name"] for col in columns_info if col["name"] not in exclude]
