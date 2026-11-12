"""数据库迁移 SQL 目录；当前只有第一版 000_schema.sql。

迁移执行入口是 `app.repos.database.run_migrations()`，它按文件名顺序执行本目录下的
所有 `.sql` 文件；这里不直接放 Python 逻辑，避免和 repos 层职责重叠。
"""
