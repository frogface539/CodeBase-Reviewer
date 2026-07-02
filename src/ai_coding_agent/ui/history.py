"""History formatting helpers for user interfaces."""

from ai_coding_agent.core import ActivityRecord, AgentResult


def format_history(
    runs: list[AgentResult],
    activities: list[ActivityRecord] | None = None,
) -> str:
    """Format run and repository activity history as Markdown."""

    activity_items = activities or []
    if not runs and not activity_items:
        return "No runs yet."

    lines = ["## Run History"]
    for index, item in enumerate(_merge_history(runs, activity_items), start=1):
        if isinstance(item, AgentResult):
            lines.extend(_format_agent_run(index, item))
        else:
            lines.extend(_format_activity(index, item))
    return "\n".join(lines)


def _merge_history(
    runs: list[AgentResult],
    activities: list[ActivityRecord],
) -> list[AgentResult | ActivityRecord]:
    return sorted(
        [*runs, *activities],
        key=lambda item: item.created_at,
        reverse=True,
    )


def _format_agent_run(index: int, run: AgentResult) -> list[str]:
    command = (
        " ".join(run.test_result.command)
        if run.test_result is not None
        else "Not provided"
    )
    return [
        f"### {index}. Agent: {run.request.instruction}",
        f"- Time: `{run.created_at.isoformat()}`",
        f"- Repository: `{run.request.repository_path}`",
        f"- Summary: {run.summary}",
        f"- Patch applied: `{run.patch_applied}`",
        f"- Fix attempts: `{run.fix_attempts}`",
        f"- Test command: `{command}`",
        f"- Test status: {format_test_status(run)}",
        "",
    ]


def _format_activity(index: int, record: ActivityRecord) -> list[str]:
    return [
        f"### {index}. {record.activity_type}: {record.title}",
        f"- Time: `{record.created_at.isoformat()}`",
        f"- Repository: `{record.repository_path}`",
        f"- Summary: {record.summary}",
        "",
    ]


def format_test_status(run: AgentResult) -> str:
    """Format the verification status for one run."""

    if run.test_result is None:
        return "Not run"
    if run.test_result.succeeded:
        return "Passed"
    return f"Failed with exit code `{run.test_result.return_code}`"
