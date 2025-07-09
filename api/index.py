from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import tempfile
import pdfplumber
import re
import os

app = FastAPI()

@app.post("/parse-fifththird")
async def parse_fifththird(
    pdf: UploadFile = File(...),
    expected_count: Optional[int] = Form(None),
    expected_total: Optional[float] = Form(None)
):
    # Save uploaded file to temp location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        contents = await pdf.read()
        tmp.write(contents)
        tmp_path = tmp.name

    # Convert PDF to text using pdfplumber (Vercel-compatible)
    full_text = ""
    with pdfplumber.open(tmp_path) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"

    os.remove(tmp_path)

    # Parse check triplets from full text
    all_parts = full_text.split()
    checks = []
    i = 0
    while i + 2 < len(all_parts):
        a, b, c = all_parts[i], all_parts[i+1], all_parts[i+2]
        if re.match(r"^\d{3,4}$", a) and re.match(r"^\d{2}/\d{2}$", b) and re.match(r"^[\d,]+\.\d{2}$", c):
            checks.append({
                "check_number": a,
                "date": f"2024/{b}",
                "amount": -float(c.replace(",", ""))
            })
        i += 1

    total = round(sum(c["amount"] for c in checks), 2)
    count = len(checks)

    if expected_count is not None and count != expected_count:
        raise HTTPException(status_code=422, detail=f"Expected {expected_count} checks, found {count}")

    if expected_total is not None and round(total, 2) != round(expected_total, 2):
        raise HTTPException(status_code=422, detail=f"Check total mismatch: found {total}, expected {expected_total}")

    return JSONResponse(content={"checks": checks, "count": count, "total": total})
