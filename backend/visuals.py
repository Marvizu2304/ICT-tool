from __future__ import annotations
import io, os, json, base64, datetime
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import pandas as pd
from pydantic import BaseModel, Field

class ChartSpec(BaseModel):
    kind: str = Field(description="one of line, bar, pie, scatter, area")
    title: str | None = None
    x: str | None = Field(default=None, description="x axis column")
    y: List[str] | None = Field(default=None, description="one or more y columns")
    groupby: str | None = Field(default=None, description="optional category to split the chart")
    top_n: int | None = Field(default=None, description="optional top N filter for categorical plots")

class ChartSpecSet(BaseModel):
    charts: List[ChartSpec]

def render_charts(df: pd.DataFrame, spec_set: ChartSpecSet, out_dir: str) -> list[str]:
    os.makedirs(out_dir, exist_ok=True)
    files = []
    for i, spec in enumerate(spec_set.charts, start=1):
        fig = plt.figure()  # Single chart per figure (no subplots), no explicit colors or styles
        ax = plt.gca()
        title = spec.title or f"Chart {i}"

        # Basic dispatch by kind
        if spec.kind in {"line", "area"} and spec.x and spec.y:
            for col in spec.y:
                ax.plot(df[spec.x], df[col], label=col)  # no explicit colors
            ax.set_xlabel(spec.x)
            ax.set_ylabel(", ".join(spec.y))
            ax.set_title(title)
            ax.legend()

        elif spec.kind == "bar" and spec.x and spec.y:
            # if multiple y, stack as grouped bars
            width = 0.8 / len(spec.y)
            x_vals = range(len(df[spec.x]))
            for idx, col in enumerate(spec.y):
                ax.bar([x + idx * width for x in x_vals], df[col], width=width, label=col)
            ax.set_xticks([x + (len(spec.y)-1)*width/2 for x in x_vals])
            ax.set_xticklabels(df[spec.x].astype(str).tolist(), rotation=45, ha="right")
            ax.set_xlabel(spec.x)
            ax.set_ylabel(", ".join(spec.y))
            ax.set_title(title)
            ax.legend()

        elif spec.kind == "pie" and spec.y and len(spec.y) == 1:
            col = spec.y[0]
            values = df[col]
            labels = df[spec.x].astype(str).tolist() if spec.x else [str(i) for i in range(len(values))]
            ax.pie(values, labels=labels, autopct="%1.1f%%")
            ax.set_title(title)

        elif spec.kind == "scatter" and spec.x and spec.y and len(spec.y) == 1:
            col = spec.y[0]
            ax.scatter(df[spec.x], df[col])
            ax.set_xlabel(spec.x)
            ax.set_ylabel(col)
            ax.set_title(title)

        else:
            plt.close(fig)
            continue

        fname = os.path.join(out_dir, f"chart_{i}.png")
        fig.tight_layout()
        fig.savefig(fname, dpi=140)
        plt.close(fig)
        files.append(fname)

    return files
