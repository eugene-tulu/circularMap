from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database import query, execute_write, get_connection
from app.models import MsmeCreate, MsmeUpdate

router = APIRouter(prefix="/api/msmes", tags=["MSMEs"])


def _where(county, value_chain, ownership, search):
    conds, params = [], []
    if county:
        conds.append("county = ?"); params.append(county)
    if value_chain:
        conds.append("value_chain = ?"); params.append(value_chain)
    if ownership:
        conds.append("ownership_category = ?"); params.append(ownership)
    if search:
        conds.append("(lower(enterprise_name) LIKE ? OR lower(county) LIKE ? OR lower(ward) LIKE ?)")
        term = f"%{search.lower()}%"
        params.extend([term, term, term])
    where_sql = ("WHERE " + " AND ".join(conds)) if conds else ""
    return where_sql, params


@router.get("")
async def list_msmes(
    county: Optional[str] = None,
    value_chain: Optional[str] = None,
    ownership: Optional[str] = None,
    search: Optional[str] = None,
    sort_col: str = "enterprise_id",
    sort_dir: str = "asc",
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=5000),
):
    ALLOWED_SORT = {"enterprise_id", "enterprise_name", "county", "ward", "value_chain",
                     "ownership_category", "employees", "registration_status", "capacity_score"}
    if sort_col not in ALLOWED_SORT:
        sort_col = "enterprise_id"
    sort_dir = "DESC" if sort_dir.lower() == "desc" else "ASC"

    where_sql, params = _where(county, value_chain, ownership, search)

    total = query(f"SELECT COUNT(*) AS n FROM msmes {where_sql}", params)[0]["n"]
    rows = query(
        f"SELECT * FROM msmes {where_sql} ORDER BY {sort_col} {sort_dir} LIMIT ? OFFSET ?",
        params + [limit, (page - 1) * limit],
    )
    return {"total": total, "page": page, "limit": limit, "results": rows}


@router.get("/stats")
async def dashboard_stats(
    county: Optional[str] = None,
    value_chain: Optional[str] = None,
    ownership: Optional[str] = None,
    search: Optional[str] = None,
):
    where_sql, params = _where(county, value_chain, ownership, search)

    total = query(f"SELECT COUNT(*) AS n FROM msmes {where_sql}", params)[0]["n"]
    by_county = query(f"SELECT county, COUNT(*) AS n FROM msmes {where_sql} GROUP BY county ORDER BY n DESC", params)
    by_value_chain = query(f"SELECT value_chain, COUNT(*) AS n FROM msmes {where_sql} GROUP BY value_chain ORDER BY n DESC", params)
    by_ownership = query(f"SELECT ownership_category, COUNT(*) AS n FROM msmes {where_sql} GROUP BY ownership_category ORDER BY n DESC", params)
    by_capacity = query(f"SELECT capacity_score, COUNT(*) AS n FROM msmes {where_sql} GROUP BY capacity_score ORDER BY capacity_score", params)
    by_registration = query(f"SELECT registration_status, COUNT(*) AS n FROM msmes {where_sql} GROUP BY registration_status", params)

    registered = next((r["n"] for r in by_registration if r["registration_status"] == "Registered"), 0)
    pct_registered = round(100 * registered / total, 1) if total else 0

    return {
        "total": total,
        "counties_covered": len(by_county),
        "pct_registered": pct_registered,
        "top_value_chain": by_value_chain[0]["value_chain"] if by_value_chain else None,
        "by_county": by_county,
        "by_value_chain": by_value_chain,
        "by_ownership": by_ownership,
        "by_capacity": by_capacity,
        "by_registration": by_registration,
    }


@router.get("/{enterprise_id}")
async def get_msme(enterprise_id: int):
    rows = query("SELECT * FROM msmes WHERE enterprise_id = ?", [enterprise_id])
    if not rows:
        raise HTTPException(404, "MSME not found")
    return rows[0]


@router.post("", status_code=201)
async def create_msme(msme: MsmeCreate):
    con = get_connection()
    next_id = con.execute("SELECT COALESCE(MAX(enterprise_id), 0) + 1 FROM msmes").fetchone()[0]
    execute_write(
        """INSERT INTO msmes (enterprise_id, enterprise_name, county, sub_county, ward,
               value_chain, ownership_category, employees, registration_status,
               year_established, capacity_score, support_need, latitude, longitude)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [next_id, msme.enterprise_name, msme.county, msme.sub_county, msme.ward,
         msme.value_chain, msme.ownership_category, msme.employees, msme.registration_status,
         msme.year_established, msme.capacity_score, msme.support_need, msme.latitude, msme.longitude],
    )
    return {"enterprise_id": next_id}


@router.put("/{enterprise_id}")
async def update_msme(enterprise_id: int, msme: MsmeUpdate):
    existing = query("SELECT enterprise_id FROM msmes WHERE enterprise_id = ?", [enterprise_id])
    if not existing:
        raise HTTPException(404, "MSME not found")
    execute_write(
        """UPDATE msmes SET enterprise_name=?, county=?, sub_county=?, ward=?, value_chain=?,
               ownership_category=?, employees=?, registration_status=?, year_established=?,
               capacity_score=?, support_need=?, latitude=?, longitude=?
           WHERE enterprise_id = ?""",
        [msme.enterprise_name, msme.county, msme.sub_county, msme.ward, msme.value_chain,
         msme.ownership_category, msme.employees, msme.registration_status, msme.year_established,
         msme.capacity_score, msme.support_need, msme.latitude, msme.longitude, enterprise_id],
    )
    return {"updated": True}


@router.delete("/{enterprise_id}")
async def delete_msme(enterprise_id: int):
    existing = query("SELECT enterprise_id FROM msmes WHERE enterprise_id = ?", [enterprise_id])
    if not existing:
        raise HTTPException(404, "MSME not found")
    execute_write("DELETE FROM msmes WHERE enterprise_id = ?", [enterprise_id])
    return {"deleted": True}
