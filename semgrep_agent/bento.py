import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import click
import requests
import sh
from sh.contrib import git

from .meta import Meta
from .utils import debug_echo

bento = sh.bento.bake(
    agree=True,
    email="semgrep-agent@returntocorp.com",
    _ok_code={0, 1, 2},
    _tty_out=False,
)

ALLOWED_EVENT_TYPES = frozenset(["push", "pull_request"])


@dataclass
class Results:
    exit_code: int
    findings: Optional[List[Dict[str, Any]]]
    total_time: float

    @classmethod
    def from_sh_command(
        cls, sh_command: sh.RunningCommand, meta: Meta, elapsed: float
    ) -> "Results":
        commit_date = meta.commit.committed_datetime.isoformat()

        findings = None
        if sh_command.stdout:
            findings = json.loads(sh_command.stdout.decode())
            # Augment each findings result with commit date for slicing purposes
            for f in findings:
                f["commit_date"] = commit_date

        return cls(
            exit_code=sh_command.exit_code, findings=findings, total_time=elapsed,
        )

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "findings": len(self.findings) if self.findings else None,
            "total_time": self.total_time,
        }


def scan_pull_request(ctx: click.Context) -> sh.RunningCommand:
    env = os.environ.copy()
    if ctx.obj.config:
        env["BENTO_REGISTRY"] = ctx.obj.config

    # the github ref would be `refs/pull/<pr #>/merge` which isn't known by name here
    # the github sha seems to refer to the base on re-runs
    # so we keep our own head ref around
    real_head_sha = git("rev-parse", "HEAD").stdout.strip()

    debug_echo(
        "== [1/3] going to go back to the commit you based your pull request on…"
    )
    git.checkout(os.environ["GITHUB_BASE_REF"])
    debug_echo(git.status("--branch", "--short").stdout.decode())

    debug_echo("== [2/3] …now adding your pull request's changes back…")
    git.checkout(real_head_sha, "--", ".")
    debug_echo(git.status("--branch", "--short").stdout.decode())

    debug_echo("== [3/3] …and seeing if there are any new findings!")
    human_run = bento.check(tool="semgrep", _env=env, _out=sys.stdout, _err=sys.stderr)

    if not ctx.obj.sapp.is_configured:
        return human_run

    return bento.check(tool="semgrep", _env=env, formatter="json")


def scan_push(ctx: click.Context) -> sh.RunningCommand:
    env = os.environ.copy()
    if ctx.obj.config and ctx.obj.config.startswith("r/"):
        resp = requests.get(f"https://semgrep.live/c/{ctx.obj.config}", timeout=10)
        with Path(".bento/semgrep.yml").open("w") as fd:
            fd.write(resp.content.decode("utf-8"))

    debug_echo("== seeing if there are any findings")
    human_run = bento.check(
        tool="semgrep", all=True, _env=env, _out=sys.stdout, _err=sys.stderr
    )

    if not ctx.obj.sapp.is_configured:
        return human_run
    return bento.check(tool="semgrep", all=True, _env=env, formatter="json")


def fail_on_unknown_event() -> None:
    message = f"""
        == [ERROR] the Semgrep action was triggered by an unsupported GitHub event.

        This error is often caused by an unsupported value for `on:` in the action's configuration.
        To resolve this issue, please confirm that the `on:` key only contains values from the following list: {list(ALLOWED_EVENT_TYPES)}.
        If the problem persists, please file an issue at https://github.com/returntocorp/semgrep/issues/new/choose
    """
    message = dedent(message.strip())
    click.echo(message, err=True)
    sys.exit(2)


def scan(ctx: click.Context) -> Results:
    event_type = ctx.obj.event_type
    debug_echo(f"== triggered by a {event_type}")

    if event_type not in ALLOWED_EVENT_TYPES:
        fail_on_unknown_event()

    bento.init()

    before = time.time()
    try:
        if event_type == "pull_request":
            results = scan_pull_request(ctx)
        elif event_type == "push":
            results = scan_push(ctx)
    except sh.ErrorReturnCode as error:
        click.echo((Path.home() / ".bento" / "last.log").read_text(), err=True)
        message = f"""
        == [ERROR] `{error.full_cmd}` failed with exit code {error.exit_code}

        This is an internal error, please file an issue at https://github.com/returntocorp/semgrep/issues/new/choose
        and include the log output from above.
        """
        message = dedent(message).strip()
        click.echo(message, err=True)
        sys.exit(error.exit_code)
    after = time.time()

    return Results.from_sh_command(results, ctx.obj.meta, after - before)