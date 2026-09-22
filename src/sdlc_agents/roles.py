"""Load SDLC role definitions from config/roles.toml."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]

from sdlc_agents.config import PROJECT_ROOT

ROLES_CONFIG_PATH = PROJECT_ROOT / "config" / "roles.toml"


@dataclass(frozen=True)
class Role:
    id: str
    kind: str
    description: str
    prompt_file: str
    gepa_dataset: str
    artifact: str
    optimize: bool


@lru_cache(maxsize=1)
def load_roles(config_path: Path | None = None) -> tuple[Role, ...]:
    """Load all roles from the TOML config (order preserved)."""
    path = config_path or ROLES_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Roles config not found: {path}. Expected config/roles.toml at project root."
        )
    with path.open("rb") as f:
        data = tomllib.load(f)

    raw_roles = data.get("roles")
    if not isinstance(raw_roles, list) or not raw_roles:
        raise ValueError(f"config/roles.toml must define a non-empty [[roles]] list: {path}")

    roles: list[Role] = []
    seen: set[str] = set()
    for entry in raw_roles:
        role_id = str(entry["id"]).strip()
        if not role_id:
            raise ValueError("Each role must have a non-empty id")
        if role_id in seen:
            raise ValueError(f"Duplicate role id in config/roles.toml: {role_id}")
        seen.add(role_id)
        roles.append(
            Role(
                id=role_id,
                kind=str(entry.get("kind", "worker")),
                description=str(entry.get("description", "")),
                prompt_file=str(entry.get("prompt_file", role_id)),
                gepa_dataset=str(entry.get("gepa_dataset", f"{role_id}.json")),
                artifact=str(entry.get("artifact", "")),
                optimize=bool(entry.get("optimize", True)),
            )
        )
    return tuple(roles)


def all_role_ids(config_path: Path | None = None) -> tuple[str, ...]:
    return tuple(r.id for r in load_roles(config_path))


def optimizable_role_ids(config_path: Path | None = None) -> tuple[str, ...]:
    return tuple(r.id for r in load_roles(config_path) if r.optimize)


def get_role(role_id: str, config_path: Path | None = None) -> Role:
    for role in load_roles(config_path):
        if role.id == role_id:
            return role
    known = ", ".join(all_role_ids(config_path))
    raise KeyError(f"Unknown role '{role_id}'. Known roles: {known}")
