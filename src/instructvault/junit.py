from __future__ import annotations
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Iterable, Optional
from .eval import TestResult

def write_junit_xml(*, suite_name: str, results: Iterable[TestResult], out_path: str, timestamp: Optional[str] = None) -> None:
    results = list(results)
    tests = len(results)
    failures = sum(1 for r in results if not r.passed)
    ts = timestamp or datetime.now(timezone.utc).isoformat()

    suite = ET.Element("testsuite", {
        "name": suite_name,
        "tests": str(tests),
        "failures": str(failures),
        "errors": "0",
        "time": "0",
        "timestamp": ts,
    })

    for r in results:
        case = ET.SubElement(suite, "testcase", {"name": r.name, "classname": suite_name, "time": "0"})
        if not r.passed:
            f = ET.SubElement(case, "failure", {"message": r.error or "assertion failed", "type": "AssertionError"})
            f.text = r.error or "assertion failed"

    tree = ET.ElementTree(suite)
    ET.indent(tree, space="  ")
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
