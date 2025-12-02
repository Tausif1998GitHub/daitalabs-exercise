# backend/main.py

import os
import shutil
import uuid
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

# ----------------------------------------------------------------------
# Optional OpenAI support
# ----------------------------------------------------------------------
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if (OPENAI_API_KEY and OPENAI_AVAILABLE) else None


# ----------------------------------------------------------------------
# MongoDB
# ----------------------------------------------------------------------
MONGODB_URL = os.getenv(
    "MONGODB_URL",
    "mongodb://admin:pass1234@mongodb:27017/production?authSource=admin",
)

mongo_client = AsyncIOMotorClient(MONGODB_URL)
db = mongo_client["production"]
collection = db["items"]


# ----------------------------------------------------------------------
# FastAPI App
# ----------------------------------------------------------------------
app = FastAPI(title="Production Planning Parser")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev only. Lock in prod.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------
class ProductionItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_number: Optional[str] = None
    style: Optional[str] = None
    fabric: Optional[str] = None
    color: Optional[str] = None
    quantity: Optional[int] = None
    status: Optional[str] = None
    dates: Optional[Dict[str, Any]] = None
    raw: Optional[Dict[str, Any]] = None


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def normalize_column(c: str) -> str:
    return (
        str(c)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("/", "_")
        .replace(".", "_")
    )


def safe_to_int(value: Any) -> Optional[int]:
    """Convert quantity reliably across all Excel formats."""
    try:
        if value is None:
            return None

        if isinstance(value, int):
            return value

        v = str(value).replace(",", "").strip()
        if v.lower() in ("", "none", "nan", "null"):
            return None

        return int(float(v))
    except Exception:
        return None


def infer_status(dates: Optional[Dict[str, Any]]) -> str:
    if not dates:
        return "pending"

    joined = " ".join([str(k).lower() for k in dates.keys()])
    if "ship" in joined or "dispatch" in joined:
        return "completed"

    if any(x in joined for x in ["cut", "sew", "stitch", "process"]):
        return "in_production"

    return "pending"


async def call_openai_chat(messages):
    if not openai_client:
        return None

    try:
        def sync_call():
            return openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0
            )

        resp = await asyncio.to_thread(sync_call)
        if not resp or not resp.choices:
            return None

        return resp.choices[0].message.content
    except Exception:
        return None


def clean_document_for_json(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure Safe JSON Output: no NaN, no ObjectId, no inf."""
    out = {}
    for k, v in doc.items():
        if k == "_id":
            out[k] = str(v)
            continue

        if isinstance(v, float):
            if v != v or v in (float("inf"), float("-inf")):
                out[k] = None
            else:
                out[k] = v

        elif isinstance(v, dict):
            nested = {}
            for nk, nv in v.items():
                if isinstance(nv, float) and (nv != nv or nv in (float("inf"), float("-inf"))):
                    nested[nk] = None
                else:
                    nested[nk] = nv
            out[k] = nested

        else:
            out[k] = v

    return out


# ----------------------------------------------------------------------
# Fallback Parser (AI disabled or fails)
# ----------------------------------------------------------------------
def fallback_parse(df: pd.DataFrame) -> List[Dict[str, Any]]:
    df.columns = [normalize_column(c) for c in df.columns]

    def find(cols):
        for c in df.columns:
            for key in cols:
                if key in c:
                    return c
        return None

    order_col = find(["order", "po", "job"])
    style_col = find(["style"])
    fabric_col = find(["fabric"])
    color_col = find(["color", "colour"])
    qty_col = find(["qty", "quantity"])

    timeline_cols = [
        c for c in df.columns
        if any(k in c for k in ["cut", "sew", "ship", "vap", "feeding", "finish", "plan"])
    ]

    items = []
    for _, row in df.iterrows():
        dates = {}
        for c in timeline_cols:
            v = row.get(c)
            if pd.notna(v):
                dates[c] = v.strftime("%Y-%m-%d") if isinstance(v, datetime) else str(v)

        q = safe_to_int(row.get(qty_col)) if qty_col else None

        item = ProductionItem(
            order_number=row.get(order_col) if order_col else None,
            style=row.get(style_col) if style_col else None,
            fabric=row.get(fabric_col) if fabric_col else None,
            color=row.get(color_col) if color_col else None,
            quantity=q,
            dates=dates,
            status=infer_status(dates),
            raw={str(k): (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
        ).model_dump()

        items.append(item)

    return items


# ----------------------------------------------------------------------
# AI Parsing
# ----------------------------------------------------------------------
async def ai_map_columns(columns: List[str]) -> Dict[str, Any]:
    prompt = f"""
Map these columns to JSON:
{columns}

Return ONLY JSON:
{{
 "order_number": "...",
 "style": "...",
 "fabric": "...",
 "color": "...",
 "quantity": "...",
 "timeline_columns": [...]
}}
    """

    raw = await call_openai_chat([
        {"role": "system", "content": "Return JSON only."},
        {"role": "user", "content": prompt}
    ])

    if not raw:
        return {}

    try:
        return json.loads(raw)
    except Exception:
        return {}


async def ai_parse_row(mapping, row_dict):
    prompt = f"""
Mapping: {mapping}
Row: {row_dict}

Return STRICT JSON:
{{
 "order_number": "...",
 "style": "...",
 "fabric": "...",
 "color": "...",
 "quantity": null,
 "dates": {{}}
}}
"""

    raw = await call_openai_chat([
        {"role": "system", "content": "Return JSON only."},
        {"role": "user", "content": prompt}
    ])

    if not raw:
        return {}

    try:
        return json.loads(raw)
    except Exception:
        return {}


async def parse_excel_ai(path: str) -> List[Dict[str, Any]]:
    df = pd.read_excel(path)
    cols = list(df.columns)

    mapping = await ai_map_columns(cols)
    if not mapping:
        return fallback_parse(df)

    items = []
    for _, r in df.iterrows():
        row_dict = {}
        for c in cols:
            v = r.get(c)
            row_dict[c] = (
                v.strftime("%Y-%m-%d") if isinstance(v, datetime)
                else None if pd.isna(v)
                else str(v)
            )

        parsed = await ai_parse_row(mapping, row_dict)
        if not parsed:
            # fallback row
            items.extend(fallback_parse(pd.DataFrame([r])))
            continue

        dates = parsed.get("dates") or {}
        clean_dates = {k: str(v) for k, v in dates.items()}

        item = ProductionItem(
            order_number=parsed.get("order_number"),
            style=parsed.get("style"),
            fabric=parsed.get("fabric"),
            color=parsed.get("color"),
            quantity=safe_to_int(parsed.get("quantity")),
            dates=clean_dates,
            status=infer_status(clean_dates),
            raw=row_dict
        ).model_dump()

        items.append(item)

    return items


# ----------------------------------------------------------------------
# API Routes
# ----------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/production-items")
async def get_items():
    cursor = collection.find()
    docs = await cursor.to_list(length=None)
    cleaned = [clean_document_for_json(d) for d in docs]
    return {"items": cleaned, "total": len(cleaned)}


@app.post("/api/reset-db")
async def reset_db():
    try:
        await collection.delete_many({})
        return {"message": "Database reset successful"}
    except Exception as e:
        raise HTTPException(500, f"Failed to reset DB: {e}")


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(400, "Upload an Excel file")

    temp = f"/tmp/{uuid.uuid4().hex}.xlsx"

    try:
        with open(temp, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # AI → fallback
        try:
            items = await asyncio.wait_for(parse_excel_ai(temp), timeout=90)
        except Exception:
            df = pd.read_excel(temp)
            items = fallback_parse(df)

        # ------------------------------------------------------------------
        # Smart Relaxed Filtering (THIS FIXES YOUR ISSUE)
        # ------------------------------------------------------------------
        valid = []
        for it in items:
            raw_o = it.get("order_number")
            raw_q = it.get("quantity")

            # Order number normalize
            o = str(raw_o).strip() if raw_o else None
            if o and o.lower() in ("none", "nan", "null", ""):
                o = None

            # Quantity normalize
            q = safe_to_int(raw_q)

            # Reject only if BOTH are missing
            if not o and q is None:
                continue

            it["order_number"] = o
            it["quantity"] = q

            valid.append(it)

        if valid:
            await collection.insert_many(valid)

        return {"message": "ok", "inserted": len(valid)}

    finally:
        if os.path.exists(temp):
            os.remove(temp)