"""
TinkerPilot CLI - `tp` command.
Provides quick access to all TinkerPilot features from the terminal.
"""

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

app = typer.Typer(
    name="tp",
    help="TinkerPilot - Local AI assistant for developers",
    no_args_is_help=True,
)
console = Console()


# ─── Chat / Ask ───────────────────────────────────────────────


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask"),
    no_rag: bool = typer.Option(
        False, "--no-rag", help="Skip document search, use general knowledge"
    ),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of context chunks to retrieve"),
):
    """Ask a question (uses RAG over indexed documents by default)."""
    if no_rag:
        from app.core.llm import generate

        console.print("[dim]Generating answer (no RAG)...[/dim]")
        answer = generate(question)
        console.print()
        console.print(Markdown(answer))
    else:
        from app.core.rag import query_rag

        console.print("[dim]Searching documents and generating answer...[/dim]")
        result = query_rag(question, top_k=top_k)
        console.print()
        console.print(Markdown(result["answer"]))

        if result["sources"]:
            console.print()
            console.print("[bold]Sources:[/bold]")
            for src in result["sources"]:
                loc = src["filename"]
                if src.get("line_start"):
                    loc += f":{src['line_start']}"
                console.print(f"  [{src['index']}] {loc} (relevance: {src['relevance']})")


# ─── Ingest ───────────────────────────────────────────────────


@app.command()
def ingest(
    path: str = typer.Argument(..., help="File or directory path to ingest"),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", "-r/-R"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Tag for the ingested documents"),
):
    """Ingest files or directories into the knowledge base."""
    from app.core.rag import ingest_file, ingest_directory

    target = Path(path).expanduser().resolve()
    if not target.exists():
        console.print(f"[red]Path not found: {path}[/red]")
        raise typer.Exit(1)

    if target.is_file():
        console.print(f"Ingesting file: {target.name}")
        result = ingest_file(str(target), tag=tag)
        console.print(f"  Chunks: {result['chunk_count']}")
        console.print("[green]Done.[/green]")
    else:
        console.print(f"Ingesting directory: {target}")
        results = ingest_directory(str(target), recursive=recursive, tag=tag)
        total_chunks = sum(r.get("chunk_count", 0) for r in results)
        console.print(f"  Files: {len(results)}, Total chunks: {total_chunks}")
        errors = [r for r in results if "error" in r]
        if errors:
            console.print(f"  [yellow]Errors: {len(errors)}[/yellow]")
        console.print("[green]Done.[/green]")


# ─── Search ───────────────────────────────────────────────────


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-n"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag"),
    folder: Optional[str] = typer.Option(None, "--folder", "-f", help="Search within a specific folder/project"),
):
    """Search across all indexed documents, tasks, and meetings."""
    from app.db.vector import query_collection

    console.print(f"[dim]Searching for: {query}[/dim]")
    
    where_clauses = {}
    if tag:
        where_clauses["tag"] = tag
    if folder:
        # Resolve to absolute path for filtering
        folder_path = str(Path(folder).expanduser().resolve())
        # Note: ChromaDB $contains requires where condition correctly setup
        # If there are multiple clauses, we must use $and.
        where_clauses["filepath"] = {"$contains": folder_path}
        
    where = None
    if len(where_clauses) == 1:
        where = where_clauses
    elif len(where_clauses) > 1:
        where = {"$and": [{k: v} for k, v in where_clauses.items()]}
            
    results = query_collection(query, n_results=limit, where=where)

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    if not docs:
        console.print("[yellow]No results found.[/yellow]")
        return

    for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists)):
        relevance = round(1 - dist, 3) if dist else 0
        filename = meta.get("filename", "unknown")
        line = meta.get("line_start", "")
        loc = f"{filename}:{line}" if line else filename

        console.print(
            Panel(
                doc[:300] + ("..." if len(doc) > 300 else ""),
                title=f"[bold]{loc}[/bold] (relevance: {relevance})",
                border_style="blue",
            )
        )


# ─── Transcribe ───────────────────────────────────────────────


@app.command()
def transcribe(
    audio_file: str = typer.Argument(..., help="Path to audio file"),
    language: Optional[str] = typer.Option(None, "--language", "-l"),
    summarize: bool = typer.Option(True, "--summarize/--no-summarize", "-s/-S"),
):
    """Transcribe an audio file and optionally summarize it."""
    from app.core.moonshine_stt import transcribe_file

    path = Path(audio_file).expanduser().resolve()
    if not path.exists():
        console.print(f"[red]File not found: {audio_file}[/red]")
        raise typer.Exit(1)

    console.print(f"[dim]Transcribing: {path.name}...[/dim]")
    result = transcribe_file(str(path), language=language)

    console.print()
    console.print(Panel(result["text"], title="Transcript", border_style="green"))
    console.print(f"Language: {result['language']} (confidence: {result['language_probability']})")

    if summarize and result["text"].strip():
        console.print()
        console.print("[dim]Generating summary...[/dim]")

        from app.core.llm import generate

        prompt = f"""Summarize this meeting transcript. Include key decisions and action items.

Transcript:
{result["text"][:6000]}"""

        summary = generate(prompt, temperature=0.3)
        console.print()
        console.print(Panel(Markdown(summary), title="Summary", border_style="cyan"))


# ─── Tasks ────────────────────────────────────────────────────


@app.command(name="tasks")
def list_tasks(
    status: Optional[str] = typer.Option(
        None, "--status", "-s", help="Filter: todo, in_progress, done"
    ),
):
    """List tasks."""
    from app.db.sqlite import get_session
    from app.db.models import Task
    from sqlmodel import select

    with get_session() as session:
        query = select(Task)
        if status:
            query = query.where(Task.status == status)
        tasks = session.exec(query.order_by(Task.created_at.desc())).all()

    if not tasks:
        console.print("[yellow]No tasks found.[/yellow]")
        return

    table = Table(title="Tasks")
    table.add_column("ID", style="dim")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Priority")
    table.add_column("Due")

    status_colors = {"todo": "white", "in_progress": "yellow", "done": "green"}
    priority_colors = {"high": "red", "medium": "yellow", "low": "dim"}

    for t in tasks:
        sc = status_colors.get(t.status, "white")
        pc = priority_colors.get(t.priority, "white")
        table.add_row(
            str(t.id),
            t.title,
            f"[{sc}]{t.status}[/{sc}]",
            f"[{pc}]{t.priority}[/{pc}]",
            t.due_date or "-",
        )

    console.print(table)


@app.command(name="add-task")
def add_task(
    title: str = typer.Argument(..., help="Task title"),
    priority: str = typer.Option("medium", "--priority", "-p", help="low, medium, high"),
    due: Optional[str] = typer.Option(None, "--due", "-d", help="Due date (YYYY-MM-DD)"),
):
    """Add a new task."""
    from app.db.sqlite import get_session
    from app.db.models import Task

    with get_session() as session:
        task = Task(title=title, priority=priority, due_date=due)
        session.add(task)
        session.commit()
        session.refresh(task)
        console.print(f"[green]Task #{task.id} created: {title}[/green]")


@app.command()
def done(
    task_id: int = typer.Argument(..., help="Task ID to mark as done"),
):
    """Mark a task as done."""
    import datetime
    from app.db.sqlite import get_session
    from app.db.models import Task

    with get_session() as session:
        task = session.get(Task, task_id)
        if not task:
            console.print(f"[red]Task #{task_id} not found.[/red]")
            raise typer.Exit(1)
        task.status = "done"
        task.updated_at = datetime.datetime.now().isoformat()
        session.add(task)
        session.commit()
        console.print(f"[green]Task #{task_id} marked as done: {task.title}[/green]")


# ─── Explain ──────────────────────────────────────────────────


@app.command()
def explain(
    filepath: str = typer.Argument(..., help="File to explain"),
    question: Optional[str] = typer.Option(
        None, "--question", "-q", help="Specific question about the file"
    ),
):
    """Explain a code file or script."""
    from app.core.llm import generate

    path = Path(filepath).expanduser().resolve()
    if not path.exists():
        console.print(f"[red]File not found: {filepath}[/red]")
        raise typer.Exit(1)

    content = path.read_text(encoding="utf-8", errors="replace")

    console.print(f"[dim]Analyzing: {path.name}...[/dim]")

    q_part = f"\n\nSpecific question: {question}" if question else ""
    prompt = f"""Filename: {path.name}
```
{content[:6000]}
```
{q_part}

Explain what this code does. Cover purpose, key functions, important logic, and potential issues."""

    explanation = generate(
        prompt,
        system_prompt="You are a senior developer explaining code. Be clear and concise.",
        temperature=0.3,
    )
    console.print()
    console.print(Markdown(explanation))


# ─── Convert ─────────────────────────────────────────────────


@app.command()
def convert(
    filepath: str = typer.Argument(..., help="File to convert"),
    to: str = typer.Option(..., "--to", "-t", help="Target format: json, csv, pdf"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Convert files between formats (csv->json, json->csv, image->pdf)."""
    path = Path(filepath).expanduser().resolve()
    if not path.exists():
        console.print(f"[red]File not found: {filepath}[/red]")
        raise typer.Exit(1)

    src_ext = path.suffix.lower()
    to = to.lower().lstrip(".")

    if src_ext == ".csv" and to == "json":
        import csv as csv_mod

        with open(path, "r", encoding="utf-8") as f:
            reader = csv_mod.DictReader(f)
            data = list(reader)
        out_path = output or str(path.with_suffix(".json"))
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        console.print(f"[green]Converted {path.name} -> {out_path} ({len(data)} rows)[/green]")

    elif src_ext == ".json" and to == "csv":
        import csv as csv_mod

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
        if not data:
            console.print("[red]Empty JSON data.[/red]")
            raise typer.Exit(1)
        out_path = output or str(path.with_suffix(".csv"))
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            writer = csv_mod.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        console.print(f"[green]Converted {path.name} -> {out_path} ({len(data)} rows)[/green]")

    elif src_ext in (".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp") and to == "pdf":
        try:
            import img2pdf
        except ImportError:
            console.print("[red]img2pdf not installed: pip install img2pdf[/red]")
            raise typer.Exit(1)
        out_path = output or str(path.with_suffix(".pdf"))
        with open(path, "rb") as img_f, open(out_path, "wb") as pdf_f:
            pdf_f.write(img2pdf.convert(img_f.read()))
        console.print(f"[green]Converted {path.name} -> {out_path}[/green]")

    else:
        console.print(f"[red]Unsupported conversion: {src_ext} -> .{to}[/red]")
        console.print("Supported: csv->json, json->csv, image->pdf")
        raise typer.Exit(1)


# ─── Command Helper ──────────────────────────────────────────


@app.command()
def cmd(
    description: Optional[str] = typer.Argument(
        None, help="Natural language description of what you want to do"
    ),
    voice: bool = typer.Option(False, "--voice", "-v", help="Use voice input instead of text"),
    duration: int = typer.Option(10, "--duration", "-d", help="Max recording duration in seconds"),
):
    """Convert natural language to a shell command."""
    from app.core.llm import generate

    if voice:
        import sounddevice as sd
        import soundfile as sf
        import tempfile
        import time

        sample_rate = 16000
        console.print(f"[bold cyan]Recording up to {duration} seconds... Speak now.[/bold cyan]")

        start_time = time.time()
        audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype="float32")

        try:
            while time.time() - start_time < duration:
                elapsed = time.time() - start_time
                sys.stdout.write(
                    f"\r⏱️  Recording: {elapsed:.1f}s / {duration}s  (Press Ctrl+C to stop early) "
                )
                sys.stdout.flush()
                time.sleep(0.1)
        except KeyboardInterrupt:
            sd.stop()
            sys.stdout.write("\n")
            console.print("[yellow]Recording stopped early.[/yellow]")

        sys.stdout.write("\r" + " " * 80 + "\r")  # Clear the line

        elapsed_exact = min(time.time() - start_time, duration)
        actual_frames = int(elapsed_exact * sample_rate)
        if actual_frames < len(audio):
            audio = audio[:actual_frames]

        console.print(f"[dim]Recording complete ({elapsed_exact:.1f}s). Transcribing...[/dim]")

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, audio, sample_rate)
            tmp_path = tmp.name

        from app.core.moonshine_stt import transcribe_file

        result = transcribe_file(tmp_path)

        Path(tmp_path).unlink(missing_ok=True)
        
        description = result["text"].strip()
        if not description:
            console.print("[red]Could not hear anything. Please try again.[/red]")
            return
        console.print(f"[green]Heard: {description}[/green]")
    elif not description:
        console.print("[red]Error: Must provide a description or use --voice[/red]")
        raise typer.Exit(1)

    prompt = f"""Convert this to a shell command (macOS/zsh):
"{description}"
Output ONLY the command, nothing else. If dangerous, prefix with "# WARNING: "."""

    command = generate(
        prompt,
        system_prompt="You convert natural language to shell commands. Output ONLY the command.",
        temperature=0.1,
        max_tokens=200,
    )
    console.print()
    console.print(f"[bold cyan]$ {command.strip()}[/bold cyan]")
    console.print("[dim]Review before running. Not auto-executed.[/dim]")


# ─── Git Digest ───────────────────────────────────────────────


@app.command(name="git-digest")
def git_digest_cmd(
    repo_path: str = typer.Argument(".", help="Path to git repository"),
    commits: int = typer.Option(20, "--commits", "-n", help="Number of recent commits"),
):
    """Summarize recent git activity in a repository."""
    import subprocess
    from app.core.llm import generate

    repo = Path(repo_path).expanduser().resolve()
    if not (repo / ".git").exists():
        console.print(f"[red]Not a git repository: {repo}[/red]")
        raise typer.Exit(1)

    result = subprocess.run(
        ["git", "log", f"--max-count={commits}", "--oneline", "--no-merges"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        timeout=10,
    )
    git_log = result.stdout.strip()

    if not git_log:
        console.print("[yellow]No commits found.[/yellow]")
        return

    console.print("[dim]Summarizing git activity...[/dim]")
    prompt = f"""Summarize this git activity. Group related commits and highlight important changes.

{git_log}"""

    digest = generate(prompt, temperature=0.3)
    console.print()
    console.print(Markdown(digest))


# ─── Git Commit Msg ───────────────────────────────────────────


@app.command(name="git-commit-msg")
def git_commit_msg_cmd(
    repo_path: str = typer.Argument(".", help="Path to git repository"),
):
    """Generate a commit message based on working directory changes."""
    import subprocess
    from app.core.llm import generate

    repo = Path(repo_path).expanduser().resolve()
    if not (repo / ".git").exists():
        console.print(f"[red]Not a git repository: {repo}[/red]")
        raise typer.Exit(1)

    # Check for staged changes
    staged_diff = subprocess.run(
        ["git", "diff", "--staged"], cwd=str(repo), capture_output=True, text=True
    ).stdout.strip()

    # Check for unstaged changes
    unstaged_diff = subprocess.run(
        ["git", "diff"], cwd=str(repo), capture_output=True, text=True
    ).stdout.strip()

    if not staged_diff and not unstaged_diff:
        # Check for untracked files
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=str(repo),
            capture_output=True,
            text=True,
        ).stdout.strip()
        if untracked:
            console.print(
                "[yellow]Only untracked files found. Please `git add` them first to generate a message.[/yellow]"
            )
        else:
            console.print("[yellow]No changes found to commit.[/yellow]")
        return

    # Prefer staged, fallback to unstaged
    diff_to_use = staged_diff if staged_diff else unstaged_diff
    status_msg = "staged" if staged_diff else "unstaged"

    console.print(f"[dim]Analyzing {status_msg} changes to generate commit message...[/dim]")

    # Limit diff size to prevent context window explosion
    if len(diff_to_use) > 12000:
        diff_to_use = diff_to_use[:12000] + "\n... [diff truncated]"

    prompt = f"""Generate a concise, professional git commit message based on the following code changes.
Use the conventional commits format (e.g., feat: added login, fix: resolved crash, refactor: cleaned up layout).
Output ONLY the commit message, nothing else. Do not wrap it in quotes.

Changes:
{diff_to_use}"""

    msg = generate(
        prompt,
        system_prompt="You are a senior developer writing a commit message. Output ONLY the message.",
        temperature=0.2,
    )

    console.print("\n[bold green]Suggested Commit Message:[/bold green]")
    console.print(f"[cyan]{msg.strip()}[/cyan]\n")

    if not staged_diff:
        console.print(
            "[dim]Note: These changes are not staged yet. Run `git add` before committing.[/dim]"
        )


# ─── Digest ───────────────────────────────────────────────────


@app.command()
def digest():
    """Show your daily briefing (tasks, meetings, notes)."""
    from app.db.sqlite import get_session, init_db
    from app.db.models import Task, Meeting
    from app.config import ensure_directories

    ensure_directories()
    init_db()

    # Gather data
    with get_session() as session:
        from sqlmodel import select
        pending = session.exec(select(Task).where(Task.status.in_(["todo", "in_progress"]))).all()
        recent_meetings = session.exec(select(Meeting).order_by(Meeting.date.desc()).limit(3)).all()

    console.print(Panel("[bold]Daily Digest[/bold]", border_style="cyan"))

    # Tasks
    if pending:
        console.print("\n[bold]Pending Tasks:[/bold]")
        for t in pending:
            icon = {"high": "[red]![/red]", "medium": "[yellow]-[/yellow]", "low": "[dim].[/dim]"}
            console.print(f"  {icon.get(t.priority, '-')} {t.title} [{t.status}]")
    else:
        console.print("\n[green]No pending tasks.[/green]")

    # Recent meetings
    if recent_meetings:
        console.print("\n[bold]Recent Meetings:[/bold]")
        for m in recent_meetings:
            summary = ""
            if m.summary:
                try:
                    s = json.loads(m.summary)
                    summary = s.get("summary", "")[:100]
                except json.JSONDecodeError:
                    summary = m.summary[:100]
            console.print(f"  - {m.title} ({m.date[:10]})")
            if summary:
                console.print(f"    [dim]{summary}[/dim]")

    # Notes
    try:
        from app.integrations.apple_notes import get_notes

        notes = get_notes(limit=3)
        if notes:
            console.print("\n[bold]Recent Notes:[/bold]")
            for n in notes:
                title = n.get("title", "Untitled")
                console.print(f"  - {title}")
    except Exception:
        pass

    console.print()


# ─── Listen (Speech-to-Text) ─────────────────────────────────


@app.command()
def listen(
    duration: int = typer.Option(10, "--duration", "-d", help="Recording duration in seconds"),
    language: Optional[str] = typer.Option(None, "--language", "-l"),
):
    """Record audio and transcribe (speech-to-text)."""
    import sounddevice as sd
    import soundfile as sf
    import tempfile
    import time

    sample_rate = 16000
    console.print(f"[bold cyan]Recording up to {duration} seconds... Speak now.[/bold cyan]")

    start_time = time.time()
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype="float32")

    try:
        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            sys.stdout.write(
                f"\r⏱️  Recording: {elapsed:.1f}s / {duration}s  (Press Ctrl+C to stop early) "
            )
            sys.stdout.flush()
            time.sleep(0.1)
    except KeyboardInterrupt:
        sd.stop()
        sys.stdout.write("\n")
        console.print("[yellow]Recording stopped early.[/yellow]")

    sys.stdout.write("\r" + " " * 80 + "\r")  # Clear the line

    elapsed_exact = min(time.time() - start_time, duration)
    actual_frames = int(elapsed_exact * sample_rate)
    if actual_frames < len(audio):
        audio = audio[:actual_frames]

    console.print(f"[dim]Recording complete ({elapsed_exact:.1f}s). Transcribing...[/dim]")

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, audio, sample_rate)
        tmp_path = tmp.name

    from app.core.moonshine_stt import transcribe_file

    result = transcribe_file(tmp_path, language=language)

    Path(tmp_path).unlink(missing_ok=True)

    console.print()
    console.print(result["text"])


# ─── Speak (Text-to-Speech) ───────────────────────────────────


@app.command()
def speak(
    text: str = typer.Argument(..., help="Text to speak aloud"),
    voice: Optional[str] = typer.Option(
        None, "--voice", "-v", help="Voice name (heart, bella, adam, michael)"
    ),
    speed: float = typer.Option(1.0, "--speed", "-s", help="Speech speed (0.5-2.0)"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Save to WAV file instead of playing"
    ),
    summarize: bool = typer.Option(
        False, "--summarize", help="Summarize the text/file concisely before speaking"
    ),
):
    """Convert text to speech using Kokoro TTS."""
    from app.core.tts import speak as tts_speak, list_voices

    # Check if the input text is a valid file path
    path = Path(text).expanduser().resolve()
    if path.is_file():
        try:
            content = path.read_text(encoding="utf-8").strip()
            if content:
                text = content
                console.print(f"[dim]Reading from file: {path.name}...[/dim]")
            else:
                console.print(f"[yellow]File {path.name} is empty.[/yellow]")
                raise typer.Exit(1)
        except UnicodeDecodeError:
            pass  # Fall back to raw text if it's binary or invalid

    if summarize:
        from app.core.llm import generate

        console.print("[dim]Generating a quick summary to speak...[/dim]")
        prompt = f"""Summarize the following text cleanly and conversationally. Do NOT use markdown tables, asterisks, or complex formatting. Output ONLY spoken words:

{text[:15000]}"""
        text = generate(prompt, system_prompt="You summarize text into conversational scripts suitable for text-to-speech. Concise and clear.", temperature=0.3)
        console.print(f"\n[bold green]Summary:[/bold green]\n{text}\n")

    if output:
        console.print("[dim]Generating speech...[/dim]")
        wav_path = tts_speak(text, voice=voice, speed=speed, output_path=output)
        console.print(f"[green]Audio saved to: {output}[/green]")
    else:
        # Play the audio as it's being generated (Streaming TTS)
        try:
            import sounddevice as sd
            import threading
            import queue
            from app.core.tts import stream_audio_blocks, SAMPLE_RATE
            
            audio_queue = queue.Queue()
            
            def producer():
                for audio_chunk in stream_audio_blocks(text, voice=voice, speed=speed):
                    audio_queue.put(audio_chunk)
                audio_queue.put(None)
                
            threading.Thread(target=producer, daemon=True).start()
            
            console.print("[dim]Generating and streaming speech...[/dim]")
            while True:
                chunk = audio_queue.get()
                if chunk is None:
                    break
                sd.play(chunk, SAMPLE_RATE)
                sd.wait()
                
        except Exception as e:
            console.print(f"[yellow]Could not play audio: {e}[/yellow]")


@app.command()
def voices():
    """List available TTS voices."""
    from app.core.tts import list_voices

    table = Table(title="Available TTS Voices")
    table.add_column("Name", style="cyan")
    table.add_column("Voice ID", style="dim")

    for name, voice_id in list_voices().items():
        table.add_row(name, voice_id)

    console.print(table)


# ─── Server ──────────────────────────────────────────────────


serve_app = typer.Typer(help="Manage the TinkerPilot API server.", no_args_is_help=False)


def get_pid_file():
    from app.config import USER_DATA_DIR
    return USER_DATA_DIR / "server.pid"


@serve_app.callback(invoke_without_command=True)
def serve_main(
    ctx: typer.Context,
    host: str = typer.Option("127.0.0.1", "--host", "-h"),
    port: int = typer.Option(8000, "--port", "-p"),
    background: bool = typer.Option(False, "--background", "-b", help="Run in background"),
):
    """Manage the TinkerPilot API server."""
    if ctx.invoked_subcommand is None:
        # Default behavior: tp serve -> starts the server
        # Must pass all defaults explicitly — calling a @command fn directly gives OptionInfo objects otherwise
        start(
            host=host,
            port=port,
            background=background,
            log_level="info",
            force_console=False,
            no_open=False,
        )


@serve_app.command("start")
def start(
    host: str = typer.Option("127.0.0.1", "--host", "-h"),
    port: int = typer.Option(8000, "--port", "-p"),
    background: bool = typer.Option(False, "--background", "-b", help="Run in background"),
    log_level: str = typer.Option("info", "--log-level", help="Logging level (info, debug, warning, error)"),
    force_console: bool = typer.Option(False, "--console", help="Force foreground even if background is requested"),
    no_open: bool = typer.Option(False, "--no-open", help="Don't auto-open browser"),
):
    """Start the TinkerPilot API server."""
    import uvicorn
    import webbrowser
    import threading
    import time
    import os
    import subprocess
    import signal

    pid_file = get_pid_file()

    # Determine foreground vs background
    # --console (force_console) takes precedence over -b
    is_background = background and not force_console

    # When running as the background worker child (--console), skip PID checks.
    # The parent already wrote the PID file with our PID.
    if not force_console:
        # Check if already running
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text().strip())
                os.kill(pid, 0)
                console.print(f"[yellow]TinkerPilot server is already running (PID: {pid}).[/yellow]")
                console.print("Use [bold]tp serve stop[/bold] to stop it.")
                return
            except (ValueError, ProcessLookupError, PermissionError):
                pid_file.unlink()

    if is_background:
        # Use the installed 'tp' binary to spawn the background server.
        import pathlib
        tp_bin = pathlib.Path(sys.executable).parent / "tp"
        cmd = [str(tp_bin), "serve", "start", "--host", host, "--port", str(port), "--console", "--log-level", log_level, "--no-open"]

        env = os.environ.copy()

        # Open a log file for output
        from app.config import USER_DATA_DIR
        log_path = USER_DATA_DIR / "server.log"
        log_file = open(log_path, "w")  # Overwrite old log on each start

        process = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=log_file,
            stdin=subprocess.DEVNULL,
            start_new_session=True,  # Detach from current session
            env=env
        )

        # Save the CHILD's PID so stop can find it
        pid_file.write_text(str(process.pid))
        console.print(f"[bold green]TinkerPilot server started in background (PID: {process.pid})[/bold green]")
        console.print(f"Log: [dim]{log_path}[/dim]")
        console.print(f"URL: [bold blue]http://{host}:{port}[/bold blue]")
        return

    # Foreground Mode
    if not no_open:
        def launch_browser():
            time.sleep(1.5)  # Let Uvicorn boot up
            open_host = "localhost" if host in ("0.0.0.0", "127.0.0.1") else host
            webbrowser.open(f"http://{open_host}:{port}")

        threading.Thread(target=launch_browser, daemon=True).start()

    # Only write PID in foreground (non-console) mode
    if not force_console:
        pid_file.write_text(str(os.getpid()))

    try:
        console.print(f"[bold cyan]Starting TinkerPilot server at http://{host}:{port}[/bold cyan]")
        console.print(f"[dim]Log level: {log_level}[/dim]")

        # Set level globally for our app loggers
        import logging
        logging.getLogger("app").setLevel(log_level.upper())
        logging.getLogger("uvicorn.error").setLevel(log_level.upper())

        uvicorn.run("app.main:app", host=host, port=port, reload=False, log_level=log_level.lower())
    finally:
        # Cleanup PID on exit (only if we wrote it)
        if not force_console and pid_file.exists():
            pid_file.unlink()


@serve_app.command("stop")
def stop():
    """Stop all running TinkerPilot server instances."""
    import os
    import signal
    import subprocess
    import time

    killed_any = False
    pid_file = get_pid_file()

    # Step 1: Kill the PID-file tracked process
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)  # Check it's alive
            console.print(f"[dim]Stopping tracked server (PID: {pid})...[/dim]")
            os.kill(pid, signal.SIGTERM)
            for _ in range(30):
                try:
                    os.kill(pid, 0)
                    time.sleep(0.1)
                except ProcessLookupError:
                    break
            else:
                os.kill(pid, signal.SIGKILL)
            killed_any = True
        except (ValueError, ProcessLookupError, PermissionError):
            pass
        finally:
            pid_file.unlink(missing_ok=True)

    # Step 2: Broad sweep — find any remaining uvicorn processes serving app.main:app
    try:
        result = subprocess.run(
            ["pgrep", "-f", "uvicorn.*app.main:app"],
            capture_output=True, text=True
        )
        stray_pids = [int(p) for p in result.stdout.strip().splitlines() if p.strip()]
        for pid in stray_pids:
            if pid == os.getpid():
                continue  # Don't kill ourselves
            try:
                console.print(f"[dim]Stopping stray server process (PID: {pid})...[/dim]")
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.3)
                try:
                    os.kill(pid, 0)
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                killed_any = True
            except (ProcessLookupError, PermissionError):
                pass
    except FileNotFoundError:
        pass  # pgrep not available (rare on macOS/Linux)

    if killed_any:
        console.print("[green]TinkerPilot server stopped.[/green]")
    else:
        console.print("[yellow]No running TinkerPilot server found.[/yellow]")



app.add_typer(serve_app, name="serve")


# ─── Security ──────────────────────────────────────────────────


@app.command(name="check-secrets")
def check_secrets_cmd(
    directory: str = typer.Argument(".", help="Directory to scan"),
):
    """Scan a directory for hardcoded secrets, API keys, and tokens."""
    import re
    import os

    target_dir = Path(directory).expanduser().resolve()
    if not target_dir.exists():
        console.print(f"[red]Directory not found: {directory}[/red]")
        raise typer.Exit(1)

    console.print(f"[dim]Scanning {target_dir} for secrets...[/dim]\n")

    patterns = {
        "AWS Access Key": r"AKIA[0-9A-Z]{16}",
        "GitHub Token": r"gh[pousr]_[a-zA-Z0-9]{36}",
        "Hugging Face Token": r"hf_[a-zA-Z0-9]{34}",
        "Stripe Key": r"sk_live_[0-9a-zA-Z]{24}",
        "Generic Secret/Token": r"(?i)(api[_-]?key|secret|token|password)['\"]?\s*[:=]\s*['\"]([a-zA-Z0-9_\-]{12,})['\"]",
        "RSA Private Key": r"-----BEGIN " + r"RSA PRIVATE KEY-----",
    }

    ignore_dirs = {".git", ".venv", "node_modules", "out", "__pycache__", ".next", "build", "dist"}
    found_secrets = False

    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:
            if file.endswith(
                (".pyc", ".png", ".jpg", ".pdf", ".wav", ".mp3", ".mp4", ".zip", ".tar.gz", ".lock")
            ):
                continue

            filepath = Path(root) / file
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")

                for secret_name, pattern in patterns.items():
                    for match in re.finditer(pattern, content):
                        found_secrets = True
                        line_no = content.count("\n", 0, match.start()) + 1

                        # Safely redact for display
                        full_match = match.group(0)
                        if len(full_match) > 6:
                            redacted = full_match[:6] + "*" * 10 + full_match[-4:]
                        else:
                            redacted = "***REDACTED***"

                        rel_path = filepath.relative_to(target_dir)
                        console.print(f"[red]🚨 {secret_name} found![/red]")
                        console.print(f"  File:  [bold]{rel_path}:{line_no}[/bold]")
                        console.print(f"  Match: [dim]{redacted}[/dim]\n")

            except Exception:
                pass

    if not found_secrets:
        console.print("[green]✅ No secrets found! The repository looks clean.[/green]")
    else:
        console.print(
            "[yellow]⚠️  Please review and remove these secrets before committing or pushing your code.[/yellow]"
        )


if __name__ == "__main__":
    app()
