import io
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from textwrap import indent
from typing import Any
from typing import cast
from typing import Dict
from typing import Generator
from typing import Iterator
from typing import List
from typing import Optional
from typing import TextIO

import click
import sh
from sh.contrib import git

from semgrep_agent.findings import FindingSets
from semgrep_agent.semgrepdep import invoke_semgrep
from semgrep_agent.utils import get_git_repo


def get_semgrepignore(ignore_patterns: List[str]) -> TextIO:
    semgrepignore = io.StringIO()
    TEMPLATES_DIR = (Path(__file__).parent / "templates").resolve()

    semgrepignore_path = Path(".semgrepignore")
    if semgrepignore_path.is_file():
        click.echo("| using path ignore rules from .semgrepignore", err=True)
        semgrepignore.write(semgrepignore_path.read_text())
    else:
        click.echo(
            "| using default path ignore rules of common test and dependency directories",
            err=True,
        )
        semgrepignore.write((TEMPLATES_DIR / ".semgrepignore").read_text())

    if ignore_patterns:
        click.echo(
            "| adding further path ignore rules configured on the web UI", err=True
        )
        semgrepignore.write("\n# Ignores from semgrep app\n")
        semgrepignore.write("\n".join(ignore_patterns))
        semgrepignore.write("\n")

    return semgrepignore


@dataclass
class Results:
    findings: FindingSets
    total_time: float

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "findings": len(self.findings.new),
            "total_time": self.total_time,
        }


def cai(
    base_commit_ref: Optional[str],
    head_ref: Optional[str],
    semgrep_ignore: TextIO,
    this_repo_name: Optional[str],
    this_pr_id: Optional[str],
) -> None:
    invoke_semgrep(
        base_commit_ref, head_ref, semgrep_ignore, this_repo_name, this_pr_id
    )
