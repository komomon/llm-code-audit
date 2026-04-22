from __future__ import annotations

from pathlib import Path

from idor_scaffold.models import ArtifactBundle


def load_artifacts(root: Path) -> ArtifactBundle:
    files = {}
    sample_root = root / "sample_artifacts"
    for path in sample_root.rglob("*.py"):
        relative = path.relative_to(sample_root).as_posix()
        files[relative] = path.read_text(encoding="utf-8")

    prompts = {}
    prompt_root = root / "prompts"
    for path in prompt_root.glob("*.md"):
        prompts[path.stem] = path.read_text(encoding="utf-8")

    user_request = (root / "tasks" / "user-request.md").read_text(encoding="utf-8").strip()
    return ArtifactBundle(user_request=user_request, files=files, prompts=prompts)
