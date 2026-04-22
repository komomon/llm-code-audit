from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from idor_scaffold.orchestrator import ReviewOrchestrator


def main() -> None:
    orchestrator = ReviewOrchestrator(ROOT)
    result = orchestrator.run()
    print(result.render_console())


if __name__ == "__main__":
    main()
