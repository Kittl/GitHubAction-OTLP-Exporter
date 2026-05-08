import time
from pyrfc3339 import parse
import os
import json
from fastcore.xtras import obj2dict

def do_fastcore_decode(obj):
    newobj = obj2dict(obj)
    return json.dumps(newobj)

def do_time(string):
    return (int(round(time.mktime(parse(string).timetuple())) * 1000000000))

def do_time_ms(string):
    return (int(round(time.mktime(parse(string).timetuple())) * 1000))

def do_string(string):
    return str(string).lower().replace(" ", "")

def do_parse(string):
    return string != "" and string is not None and string != "None"

def check_env_vars():
    keys = ("ACTION_TOKEN","OTEL_EXPORTER_OTLP_ENDPOINT","WORKFLOW_RUN_ID","WORKFLOW_RUN_NAME")
    keys_not_set = []

    for key in keys:
        if key not in os.environ:
            keys_not_set.append(key)
    else:
        pass

    if len(keys_not_set) > 0:
        for key in keys_not_set:
            print(key + " not set")
        exit(1)


def _retrieve_env(var_name, default):
    raw = os.getenv(var_name)
    if raw is None:
        return set(default)
    return {part.strip() for part in raw.lower().split(",") if part.strip()}

# Current needed attributes for workflow span are injected in the exported
WORKFLOW_ALLOWED = _retrieve_env("GITHUB_ATTRS_ALLOW_WORKFLOW", set())

JOB_ALLOWED = _retrieve_env("GITHUB_ATTRS_ALLOW_JOB", {
    "status",
    "conclusion",
    "started_at",
    "completed_at",
    "created_at",
    "head_branch",
    "head_sha",
    "run_attempt",
    "runner_group_id",
    "runner_group_name",
    "runner_id",
    "runner_name",
})

STEP_ALLOWED = _retrieve_env("GITHUB_ATTRS_ALLOW_STEP", {
    "status",
    "conclusion",
    "number",
    "started_at",
    "completed_at",
})

ALLOWED_BY_TYPE = {
    "workflow": WORKFLOW_ALLOWED,
    "job": JOB_ALLOWED,
    "step": STEP_ALLOWED,
}


# Flatten nested dicts/lists into dotted keys.
# For lists of dicts, fields collapse onto `prefix.att`
def _flatten_object(obj, prefix=""):
    flat = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = do_string(k)
            new_prefix = f"{prefix}.{key}" if prefix else key
            if isinstance(v, (dict, list)):
                flat.update(_flatten_object(v, new_prefix))
            else:
                flat[new_prefix] = v
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                flat.update(_flatten_object(item, prefix))
            elif prefix:
                flat[prefix] = item
    return flat


def parse_attributes(obj, otype):
    allowed = ALLOWED_BY_TYPE.get(str(otype).lower(), set())
    conclusion = obj.get("conclusion") if isinstance(obj, dict) else None
    out = {}
    for name, value in _flatten_object(obj).items():
        if name not in allowed:
            continue
        if not do_parse(value):
            continue
        out[name] = str(value)
        if name.endswith("_at") and conclusion not in ("skipped", "cancelled"):
            out[name + "_ms"] = do_time_ms(value)
    return out
