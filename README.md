# Excel → Calculations → Results → Visuals

A small, production-ready template to:
1) Upload an Excel
2) Run custom formulas with pandas
3) Download a results Excel
4) Ask ChatGPT for chart ideas and render charts with matplotlib (no model code execution)

## Quickstart

### 1) Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env  # and set your OPENAI_API_KEY
uvicorn main:app --reload --port 8000
```

### 2) Web (static)
Open `web/index.html` directly in your browser, or serve it with any static server.

By default CORS allows http://localhost:5173. Adjust ALLOWED_ORIGINS in `.env` or edit the list in `main.py`.

## Customize formulas
Edit `backend/processors/formulas.py` → `apply_all()`.
Replace the sample logic with your actual business rules, calculations, and summaries.
Return a dict of `sheet_name -> DataFrame`, which will be written to the output Excel.

## How visuals work
- We detect a simple schema (numeric, categorical, time columns).
- We ask OpenAI to propose ~2-4 chart specs as JSON.
- We validate those specs and render with matplotlib.
- We never execute code from the model—only our own renderer.

## API

### POST /process
Form-data:
- `file`: Excel file (.xlsx / .xls)
- `sheet` (optional): Sheet name

Returns: an Excel file with your result sheets.

### POST /visualize
Form-data:
- `file`: Excel file (.xlsx / .xls)
- `sheet` (optional): Sheet name

Returns: a ZIP containing `chart_*.png` and `chart_plan.json`.

## Docker (optional)
```Dockerfile
# Simple dev Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend .
ENV PORT=8000
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build & run:
```bash
docker build -t excel-viz .
docker run -it --rm -p 8000:8000 -e OPENAI_API_KEY=your_key excel-viz
```

## Notes
- For Excel engine we use `openpyxl`.
- If your files are very large, consider streaming chunked processing or parquet conversion.
- For security, this app does **not** execute code returned by the LLM.


## Integrate your own calculations
1. Open `backend/processors/user_main.py` and paste your complete function `analizar_inventarios(archivo_entrada, output_path)`.

2. Save and run the backend. When you POST to `/process`, the server will call your function and return its Excel.

3. If the module or function is missing, the server falls back to the default `processors/formulas.py` pipeline.

