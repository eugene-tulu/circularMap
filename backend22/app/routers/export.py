from fastapi import APIRouter, Response
from app.database import query, get_connection
import json
import io
import os
import tempfile

router = APIRouter(prefix="/api/export", tags=["Export"])


@router.get("/geojson")
async def export_geojson():
    rows = query("SELECT * FROM msmes ORDER BY enterprise_id")
    features = []
    for r in rows:
        props = {k: v for k, v in r.items() if k not in ("latitude", "longitude")}
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["longitude"], r["latitude"]]},
            "properties": props,
        })
    geojson = {"type": "FeatureCollection", "features": features}
    return Response(
        content=json.dumps(geojson),
        media_type="application/geo+json",
        headers={"Content-Disposition": "attachment; filename=kepsa_msmes.geojson"},
    )


@router.get("/csv")
async def export_csv():
    con = get_connection()
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        path = tmp.name
    con.execute(f"COPY (SELECT * FROM msmes ORDER BY enterprise_id) TO '{path}' WITH (HEADER, DELIMITER ',')")
    with open(path, "r") as f:
        content = f.read()
    os.remove(path)
    return Response(content, media_type="text/csv",
                     headers={"Content-Disposition": "attachment; filename=kepsa_msmes.csv"})


@router.get("/parquet")
async def export_parquet():
    con = get_connection()
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
        path = tmp.name
    con.execute(f"COPY (SELECT * FROM msmes ORDER BY enterprise_id) TO '{path}' (FORMAT PARQUET)")
    with open(path, "rb") as f:
        content = f.read()
    os.remove(path)
    return Response(content, media_type="application/octet-stream",
                     headers={"Content-Disposition": "attachment; filename=kepsa_msmes.parquet"})
