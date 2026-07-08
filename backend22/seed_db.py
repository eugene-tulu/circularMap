"""
Seeds backend/data/kepsa.duckdb from backend/data/msme_data.csv.

NOTE ON SCHEMA: the reference architecture proposed normalized lookup tables
(counties / sub_counties / wards with foreign keys). For an 800-row, single-
analyst demo within a 30-day budget, that normalization buys correctness
guarantees you don't need yet and costs you three extra joins on every query.
This uses a flat/denormalized `msmes` table instead (county/sub_county/ward
as plain text columns) — same filtering behavior, less code, easy to migrate
to the normalized version later if KEPSA needs strict referential integrity
or multi-source data entry.

Run: python3 seed_db.py
"""
import duckdb
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "data", "msme_data.csv")
DB_PATH = os.path.join(HERE, "data", "kepsa.duckdb")

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

con = duckdb.connect(DB_PATH)

con.execute(f"""
    CREATE TABLE msmes AS
    SELECT * FROM read_csv('{CSV_PATH}', header=true, AUTO_DETECT=TRUE);
""")

con.execute("CREATE INDEX idx_county ON msmes(county);")
con.execute("CREATE INDEX idx_value_chain ON msmes(value_chain);")
con.execute("CREATE INDEX idx_ward ON msmes(ward);")

con.execute("""
    CREATE OR REPLACE VIEW v_county_summary AS
    SELECT county,
           COUNT(*) AS total_msmes,
           ROUND(100.0 * SUM(CASE WHEN registration_status='Registered' THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_registered,
           ROUND(AVG(capacity_score), 2) AS avg_capacity_score
    FROM msmes GROUP BY county ORDER BY total_msmes DESC;
""")
con.execute("""
    CREATE OR REPLACE VIEW v_value_chain_summary AS
    SELECT value_chain, COUNT(*) AS total_msmes, ROUND(AVG(employees), 1) AS avg_employees
    FROM msmes GROUP BY value_chain ORDER BY total_msmes DESC;
""")

count = con.execute("SELECT COUNT(*) FROM msmes").fetchone()[0]
print(f"Seeded {count} MSME records into {DB_PATH}")
con.close()
