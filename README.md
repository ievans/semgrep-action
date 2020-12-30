# Semgrepdep: Dependency Permissions Analysis

[![r2c community slack](https://img.shields.io/badge/r2c_slack-join-brightgreen?style=for-the-badge&logo=slack&labelColor=4A154B)](https://join.slack.com/t/r2c-community/shared_invite/enQtNjU0NDYzMjAwODY4LWE3NTg1MGNhYTAwMzk5ZGRhMjQ2MzVhNGJiZjI1ZWQ0NjQ2YWI4ZGY3OGViMGJjNzA4ODQ3MjEzOWExNjZlNTA)

Semgrepdep inspects PRs with yarn/pipenv lockfile changes and uses [Semgrep](https://semgrep.dev) to summarize the "permissions" in the modules and whether they changed. Permissions are coarse but roughly fall into does it use exec/equivalent (code execution), does it have any network functionality, IO functionality, use crypto libraries, etc.

This GitHub Action is an experiment built by [r2c](https://r2c.dev). If you have questions, please ask in the [r2c Slack](https://r2c.dev/slack).

## 🚨 NOTICE: experimental beta software! Nothing is guaranteed! 🚨 

To install, copy the [.github/workflows/semgrepdep.yml](.github/workflows/semgrepdep.yml) into your own repo:

    mkdir -p .github/workflows
    curl https://raw.githubusercontent.com/ievans/semgrep-action/develop/.github/workflows/semgrepdep.yml > .github/workflows/semgrepdep.yml

## Security?

Semgrepdep is a dependency itself...soooo what are the risks of adding it? You should carefully inspect the workflow file and verify that the `GITHUB_TOKEN`, which allows this bot to make comments, is passed into only Github-created actions (*not* this action) that run *after* Semgrepdep. This means that the bot will run without special priveleges that allow it to comment, and must rely on the official, Github-provided `github-script` to do the commenting.

## Will this actually detect malicious packages? 

We'll see...in a sampled assessment of a more rigorous version, it correctly identified malicious OR vulnerable packages <5% of the time. So best case, 19 out of 20 times the comment will lead you to a “this is fine” conclusion in exchange for "hmm, malicious?" the other 1 time.
