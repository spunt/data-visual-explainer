import sys

try:
    from .cli import main
except ModuleNotFoundError as e:
    if (e.name or "").split(".")[0] not in {"yaml", "jinja2", "jsonschema", "markupsafe"}:
        raise
    sys.exit(
        f"mcard needs the Python package '{e.name}', which is not installed.\n"
        "Install its three dependencies with:  python3 -m pip install pyyaml jinja2 jsonschema\n"
        "(or, from a checkout of this repository:  python3 -m pip install -e .)"
    )

sys.exit(main())
