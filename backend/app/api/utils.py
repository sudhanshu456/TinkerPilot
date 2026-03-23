"""
Developer utility API endpoints.
File conversions, code explanation, log analysis, git digest,
terminal command helper.
"""

import base64
import csv
import io
import json
import logging
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["utils"])


# --- File Conversions ---


class ConvertRequest(BaseModel):
    content: str  # raw content or base64 for binary
    from_format: str
    to_format: str


@router.post("/utils/convert/csv-to-json")
async def csv_to_json(file: UploadFile = File(...)):
    """Convert CSV file to JSON."""
    content = (await file.read()).decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    return {"data": rows, "count": len(rows), "filename": file.filename}


@router.post("/utils/convert/json-to-csv")
async def json_to_csv(file: UploadFile = File(...)):
    """Convert JSON file to CSV string."""
    content = (await file.read()).decode("utf-8", errors="replace")
    data = json.loads(content)

    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list) or not data:
        raise HTTPException(status_code=400, detail="JSON must be an array of objects")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    return {"csv": output.getvalue(), "count": len(data)}


@router.post("/utils/convert/image-to-pdf")
async def image_to_pdf(file: UploadFile = File(...)):
    """Convert image to PDF."""
    try:
        import img2pdf
    except ImportError:
        raise HTTPException(status_code=500, detail="img2pdf not installed")

    content = await file.read()
    pdf_bytes = img2pdf.convert(content)
    pdf_b64 = base64.b64encode(pdf_bytes).decode()

    return {
        "pdf_base64": pdf_b64,
        "filename": Path(file.filename).stem + ".pdf",
        "size": len(pdf_bytes),
    }


@router.post("/utils/convert/base64-encode")
async def b64_encode(file: UploadFile = File(...)):
    """Base64 encode a file."""
    content = await file.read()
    encoded = base64.b64encode(content).decode()
    return {"base64": encoded, "original_size": len(content), "encoded_size": len(encoded)}


@router.post("/utils/convert/base64-decode")
async def b64_decode(data: str):
    """Base64 decode a string."""
    try:
        decoded = base64.b64decode(data)
        return {
            "decoded_size": len(decoded),
            "preview": decoded[:200].decode("utf-8", errors="replace"),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64: {e}")


# --- AI-Powered Dev Tools ---


class ExplainRequest(BaseModel):
    content: str
    filename: Optional[str] = None
    question: Optional[str] = None


class LogAnalyzeRequest(BaseModel):
    content: str
    filename: Optional[str] = None


class CmdRequest(BaseModel):
    description: str


class GitDigestRequest(BaseModel):
    repo_path: str
    num_commits: int = 20


@router.post("/utils/explain")
async def explain_code(req: ExplainRequest):
    """Explain code or a script using LLM."""
    from app.core.llm import generate

    context = ""
    if req.filename:
        context = f"Filename: {req.filename}\n"

    question_part = ""
    if req.question:
        question_part = f"\n\nSpecific question: {req.question}"

    prompt = f"""{context}Code/Script content:
```
{req.content[:6000]}
```
{question_part}

Explain what this code does. Cover:
1. Purpose and overview
2. Key functions/components
3. Important logic or patterns
4. Any potential issues or improvements"""

    explanation = generate(
        prompt,
        system_prompt="You are a senior developer explaining code to a colleague. Be clear and concise.",
        temperature=0.3,
    )

    return {"explanation": explanation, "filename": req.filename}


@router.post("/utils/analyze-log")
async def analyze_log(req: LogAnalyzeRequest):
    """Analyze a log file for errors, patterns, and suggestions."""
    from app.core.llm import generate

    prompt = f"""Analyze this log output and provide:
1. Summary of errors and warnings found
2. Patterns or recurring issues
3. Suggested fixes or debugging steps
4. Severity assessment

Log content:
```
{req.content[:6000]}
```"""

    analysis = generate(
        prompt,
        system_prompt="You are a DevOps engineer analyzing logs. Be precise about error patterns and actionable in your suggestions.",
        temperature=0.3,
    )

    return {"analysis": analysis, "filename": req.filename}


@router.post("/utils/cmd")
async def suggest_command(req: CmdRequest):
    """Convert natural language to shell command (never auto-executes)."""
    from app.core.llm import generate

    prompt = f"""Convert this description to a shell command (macOS/zsh):

"{req.description}"

Respond with ONLY the command, no explanation. If multiple commands needed, separate with &&.
If the request is dangerous or destructive, prefix with "# WARNING: " and explain why."""

    command = generate(
        prompt,
        system_prompt="You convert natural language to shell commands. Output ONLY the command. Be safe.",
        temperature=0.1,
        max_tokens=200,
    )

    return {
        "command": command.strip(),
        "description": req.description,
        "warning": "Review before executing. Never auto-run.",
    }


@router.post("/utils/git-digest")
async def git_digest(req: GitDigestRequest):
    """Summarize recent git commits in a repository."""
    from app.core.llm import generate

    repo = Path(req.repo_path).expanduser().resolve()
    if not (repo / ".git").exists():
        raise HTTPException(status_code=400, detail="Not a git repository")

    try:
        result = subprocess.run(
            ["git", "log", f"--max-count={req.num_commits}", "--oneline", "--no-merges"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=10,
        )
        git_log = result.stdout.strip()

        if not git_log:
            return {"digest": "No commits found.", "repo": str(repo)}

        # Also get diff stats
        stat_result = subprocess.run(
            ["git", "log", f"--max-count={req.num_commits}", "--stat", "--no-merges"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=10,
        )
        git_stats = stat_result.stdout.strip()[:4000]

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Git command timed out")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Git not found on system")

    prompt = f"""Summarize the recent git activity for this repository.
Group related commits, highlight important changes, and note any patterns.

Recent commits:
{git_log}

Commit details:
{git_stats}"""

    digest = generate(
        prompt,
        system_prompt="You summarize git activity for developers. Be concise, group related changes, highlight what matters.",
        temperature=0.3,
    )

    return {"digest": digest, "repo": str(repo), "commit_count": len(git_log.strip().split("\n"))}


@router.post("/utils/test-checklist")
async def generate_test_checklist(req: ExplainRequest):
    """Generate a test/QA checklist for code or a feature."""
    from app.core.llm import generate

    prompt = f"""Generate a practical test checklist for the following code/feature.
Include: unit tests, edge cases, integration points, and manual verification steps.

{f"File: {req.filename}" if req.filename else ""}
```
{req.content[:6000]}
```"""

    checklist = generate(
        prompt,
        system_prompt="You are a QA engineer creating test checklists. Be thorough but practical.",
        temperature=0.3,
    )

    return {"checklist": checklist, "filename": req.filename}


@router.post("/utils/repro-steps")
async def suggest_repro_steps(req: ExplainRequest):
    """Suggest reproduction steps for a bug based on description/code/logs."""
    from app.core.llm import generate

    prompt = f"""Based on the following bug report/code/logs, suggest detailed reproduction steps.
Include environment setup, preconditions, exact steps, and expected vs actual behavior.

{f"File: {req.filename}" if req.filename else ""}
```
{req.content[:6000]}
```"""

    steps = generate(
        prompt,
        system_prompt="You are a senior QA engineer. Create clear, detailed reproduction steps.",
        temperature=0.3,
    )

    return {"repro_steps": steps}


# ─── Text-to-Speech ──────────────────────────────────────────


class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = None
    speed: float = 1.0


@router.post("/utils/speak")
async def text_to_speech(req: TTSRequest):
    """Generate speech audio from text using Kokoro TTS."""
    from app.core.tts import speak, list_voices

    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    try:
        output_path = speak(
            req.text,
            voice=req.voice,
            speed=req.speed,
        )
        from fastapi.responses import FileResponse

        return FileResponse(
            output_path,
            media_type="audio/wav",
            filename="speech.wav",
        )
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


@router.get("/utils/voices")
async def get_voices():
    """List available TTS voices."""
    from app.core.tts import list_voices

    return {"voices": list_voices()}
