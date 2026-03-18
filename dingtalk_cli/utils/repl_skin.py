from __future__ import annotations

from pathlib import Path

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.history import FileHistory
except ImportError:  # pragma: no cover - fallback for minimal environments
    class PromptSession:  # type: ignore[override]
        def __init__(self, *args, **kwargs) -> None:
            pass

        def prompt(self, message: str) -> str:
            return input(message)

    class WordCompleter:  # type: ignore[override]
        def __init__(self, *args, **kwargs) -> None:
            pass

    class FileHistory:  # type: ignore[override]
        def __init__(self, *args, **kwargs) -> None:
            pass


class ReplSkin:
    def __init__(self, name: str) -> None:
        self.name = name
        self.history_dir = Path.home() / ".dingtalk-cli"
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.history_dir / "history"
        self.skill_path = Path(__file__).resolve().parent.parent / "skills" / "SKILL.md"

    def print_banner(self) -> None:
        print("╭──────────────────────────────────────────────╮")
        print(f"│ {self.name:<44} │")
        print("│ Agent-friendly DingTalk document REPL        │")
        print(f"│ Skill: {str(self.skill_path):<37} │")
        print("│ 输入 help 查看命令，输入 quit 退出            │")
        print("╰──────────────────────────────────────────────╯")

    def create_prompt_session(self, commands: list[str]) -> PromptSession:
        return PromptSession(
            history=FileHistory(str(self.history_file)),
            completer=WordCompleter(commands, ignore_case=True),
        )

    def get_input(self, session: PromptSession) -> str:
        return session.prompt("dingtalk> ")

    def warning(self, message: str) -> None:
        print(f"[warn] {message}")

    def print_goodbye(self) -> None:
        print("已退出 dingtalk-cli REPL。")
