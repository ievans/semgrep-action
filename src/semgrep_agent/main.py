import os
from dataclasses import dataclass
from typing import NoReturn

import click
import sh

from semgrep_agent import semgrep
from semgrep_agent.meta import detect_meta_environment


def get_aligned_command(title: str, subtext: str) -> str:
    return f"| {title.ljust(17)} - {subtext}"


@click.command()
@click.option(
    "--baseline-ref",
    envvar="BASELINE_REF",
    type=str,
    default=None,
    show_default="detected from CI env",
)
def main(
    baseline_ref: str,
) -> None:
    click.echo("=== detecting environment", err=True)
    click.echo(
        get_aligned_command(
            "versions",
            f"on {sh.python(version=True).strip()}",
        ),
        err=True,
    )

    # Get Metadata
    Meta = detect_meta_environment()
    meta_kwargs = {}
    if baseline_ref:
        meta_kwargs["cli_baseline_ref"] = baseline_ref
    meta = Meta("noconfig", **meta_kwargs)
    click.echo(
        get_aligned_command(
            "environment",
            f"running in environment {meta.environment}, triggering event is '{meta.event_name}'",
        ),
        err=True,
    )

    committed_datetime = meta.commit.committed_datetime if meta.commit else None

    semgrep.cai(
        meta.base_commit_ref,
        meta.head_ref,
        semgrep.get_semgrepignore([]),
        meta.repo_url,
        meta.pr_id,
    )
