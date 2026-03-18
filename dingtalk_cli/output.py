from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any, TextIO

import click

from dingtalk_cli.errors import DingtalkCliError


@dataclass
class OutputState:
    json_output: bool = False
    repl_mode: bool = False


STATE = OutputState()


def set_output_state(*, json_output: bool | None = None, repl_mode: bool | None = None) -> None:
    if json_output is not None:
        STATE.json_output = json_output
    if repl_mode is not None:
        STATE.repl_mode = repl_mode


def get_output_state() -> OutputState:
    return STATE


def _write(payload: str, *, file: TextIO | None = None, human_error: bool = False) -> None:
    click.echo(payload, file=file or (sys.stderr if human_error else sys.stdout))


def emit_success(data: Any, message: str | None = None, *, file: TextIO | None = None) -> None:
    if STATE.json_output:
        _write(
            json.dumps({"ok": True, "data": data}, ensure_ascii=False, indent=2),
            file=file,
        )
        return

    if message:
        _write(message, file=file)
    if data is None:
        return
    if isinstance(data, (dict, list)):
        _write(_format_human(data), file=file)
    else:
        _write(str(data), file=file)


def emit_error(error: DingtalkCliError, *, file: TextIO | None = None) -> None:
    if STATE.json_output:
        _write(
            json.dumps({"ok": False, "error": error.to_dict()}, ensure_ascii=False, indent=2),
            file=file or sys.stdout,
        )
        return

    message = f"错误: {error.message}"
    if error.code:
        message += f" [{error.code}]"
    lines = [message]
    if error.suggestion:
        lines.append(f"建议: {error.suggestion}")
    _write("\n".join(lines), file=file, human_error=True)


def _format_human(data: Any, indent: int = 0) -> str:
    prefix = "  " * indent
    if isinstance(data, dict):
        lines: list[str] = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.append(_format_human(value, indent + 1))
            else:
                lines.append(f"{prefix}{key}: {value}")
        return "\n".join(lines)
    if isinstance(data, list):
        lines = []
        for index, item in enumerate(data):
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}[{index}]")
                lines.append(_format_human(item, indent + 1))
            else:
                lines.append(f"{prefix}- {item}")
        return "\n".join(lines)
    return f"{prefix}{data}"
