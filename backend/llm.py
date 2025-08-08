from __future__ import annotations
import os, json
from typing import Any, Dict
from pydantic import BaseModel
from openai import OpenAI

class ChartIdeaRequest(BaseModel):
    # minimal schema summary to give the model context
    columns: list[str]
    numeric_columns: list[str]
    categorical_columns: list[str]
    time_columns: list[str]

SYSTEM_PROMPT = """You are a data visualization planner. Given a dataset schema, propose 2-4 effective charts.
Return ONLY JSON with this shape:
{"charts":[
  {"kind":"line|bar|pie|scatter|area","title":"...","x":"<x-col-or-null>","y":["<one-or-more-y-cols>"],"groupby":null,"top_n":null},
  ...
]}
Rules:
- Prefer time columns for x in line/area.
- For bar charts, pick one categorical x and 1-3 numeric y.
- For pie, pick one numeric y and a categorical x (top 6 categories if many).
- Avoid suggesting columns that don't exist.
- Keep titles short and informative.
"""

def propose_chart_specs(schema: ChartIdeaRequest) -> Dict[str, Any]:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    msg = client.chat.completions.create(
        model=model,
        messages=[
            {"role":"system","content": SYSTEM_PROMPT},
            {"role":"user","content": json.dumps(schema.model_dump())}
        ],
        temperature=0.2,
        response_format={"type":"json_object"}
    )
    raw = msg.choices[0].message.content
    return json.loads(raw)
