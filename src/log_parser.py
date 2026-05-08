from io import TextIOWrapper
import os
import re
from glob import glob

log_files_catalog = {}

def catalog_log_files(dir: str) -> None:
    logs = glob('*.txt', root_dir=dir)
    log_files_catalog.update({ simplify_job_name(re.match(r'[0-9]*_(.*)\.txt', log)[1]): os.path.join(dir, log) for log in logs })

def get_log_file(job_name: str) -> str:
    return log_files_catalog[simplify_job_name(job_name)]

def simplify_job_name(job_name: str) -> str:
    return re.sub(r'[^0-9a-zA-Z]+', '', job_name).lower()

def compile_patterns(patterns_string: str | None) -> dict[str,re.Pattern]:
    patterns = []
    if patterns_string:
        patterns = [
            compile_pattern(pattern) for pattern in patterns_string.split('\n') if pattern]
    return patterns

def compile_pattern(pattern_string: str) -> [str,re.Pattern]:
    parts = pattern_string.split('=')
    return parts[0].strip(), re.compile('='.join(parts[1:]))

def parse_attributes_from_log(log_file: TextIOWrapper, patterns: dict[str,re.Pattern]) -> dict[str, str]:
    # Copy patterns dictionary as we will be removing already matched patterns from it
    patterns = dict(patterns)
    attributes = {}
    for line in log_file.readlines():
        if not patterns:
            break # No more patterns to match
        for pattern_name, pattern in list(patterns.items()):
            match = pattern.match(line)
            if match:
                attributes[pattern_name] = match.group(1)
                # Remove once match is found for efficiency
                del patterns[pattern_name]
    print("Parsed attributes from logs:", attributes)
    return attributes
