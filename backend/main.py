from __future__ import annotations
import os, io, zipfile, json, shutil, datetime
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

from processors.formulas import FormulaContext
from visuals import render_charts, ChartSpecSet, ChartSpec
from llm import propose_chart_specs, ChartIdeaRequest

# CORS
DEFAULT_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
allowed_origins = os.getenv("ALLOWED_ORIGINS")
origins = [o.strip() for o in allowed_origins.split(",")] if allowed_origins else DEFAULT_ORIGINS

app = FastAPI(title="Excel → Calculations → Results → Visuals")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True, "time": datetime.datetime.utcnow().isoformat()}

@app.post("/process")
async def process_excel(file: UploadFile = File(...), sheet: Optional[str] = Form(default=None)):
    # Save upload temporarily
    tmp_dir = "tmp"
    os.makedirs(tmp_dir, exist_ok=True)
    file_path = os.path.join(tmp_dir, f"upload_{datetime.datetime.utcnow().timestamp()}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Run formulas
    # Try user's custom script first, if present
    try:
        from processors import user_main  # optional user-provided module
        _has_user = hasattr(user_main, "analizar_inventarios")
    except Exception:
        _has_user = False

    if _has_user:
        out_tmp = os.path.join(tmp_dir, f"results_{os.path.basename(file.filename)}")
        user_main.analizar_inventarios(file_path, out_tmp)
        bio = open(out_tmp, "rb")
        headers = {"Content-Disposition": f'attachment; filename="results_{os.path.basename(file.filename)}"'}
        return StreamingResponse(bio, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)

    ctx = FormulaContext(sheet=sheet)
    df = ctx.read_excel(file_path)
    outputs = ctx.apply_all(df)

    # Build an Excel in-memory
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        for name, d in outputs.items():
            d.to_excel(writer, index=False, sheet_name=name[:31])
    bio.seek(0)

    headers = {
        "Content-Disposition": f'attachment; filename="results_{os.path.basename(file.filename)}"'
    }
    return StreamingResponse(bio, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)

@app.post("/visualize")
async def visualize(file: UploadFile = File(...), sheet: Optional[str] = Form(default=None)):
    # Save upload temporarily
    tmp_dir = "tmp"
    out_dir = os.path.join(tmp_dir, f"charts_{datetime.datetime.utcnow().timestamp()}")
    os.makedirs(tmp_dir, exist_ok=True)
    upload_path = os.path.join(tmp_dir, f"upload_{datetime.datetime.utcnow().timestamp()}_{file.filename}")
    with open(upload_path, "wb") as f:
        f.write(await file.read())

    # Read and pick a table to visualize
    df = pd.read_excel(upload_path, sheet_name=sheet or 0)

    # Simple schema detection
    numeric_cols = df.select_dtypes(include=["float64","int64","float32","int32","int"]).columns.tolist()
    time_cols = [c for c in df.columns if "date" in c.lower() or "fecha" in c.lower() or "year" in c.lower() or "month" in c.lower()]
    categorical_cols = [c for c in df.columns if c not in numeric_cols]

    schema = ChartIdeaRequest(
        columns=df.columns.tolist(),
        numeric_columns=numeric_cols,
        categorical_columns=categorical_cols,
        time_columns=time_cols
    )

    # Ask LLM for specs (no code execution)
    plan = propose_chart_specs(schema)

    # Validate with pydantic and render
    spec_set = ChartSpecSet(**plan)
    files = render_charts(df, spec_set, out_dir)

    # Zip images to return
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            zf.write(p, arcname=os.path.basename(p))
        # save the plan too
        zf.writestr("chart_plan.json", json.dumps(plan, indent=2))
    mem_zip.seek(0)

    headers = {"Content-Disposition": 'attachment; filename="charts.zip"'}
    return StreamingResponse(mem_zip, media_type="application/zip", headers=headers)

@app.get("/")
def root():
    return HTMLResponse("<h3>Server running. Use the web UI or POST /process and /visualize</h3>")


# Serve static web UI
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web"))
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h3>Server running. Upload via /process and /visualize</h3>")
