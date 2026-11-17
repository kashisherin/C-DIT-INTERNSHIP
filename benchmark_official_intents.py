"""50-case language and intent benchmark for the Official grievance assistant.

Run from the backend project root:
    .\\venv\\Scripts\\python.exe benchmark_official_intents.py

This tests only official_assistant.understand_question(). It does not read or
modify the SQLite database and does not call the Citizen Portal's Google model.
"""

from __future__ import annotations

import json
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from official_assistant import understand_question


@dataclass
class Case:
    category: str
    question: str
    expected_action: tuple[str, ...]
    department: str | None = None
    slot: int | None = None
    grievance_id: str | None = None
    search_query: str | None = None
    history: list[dict[str, str]] | None = None
    # For contextual ordinal references, either the exact ID or matching
    # department+slot is accepted because both uniquely identify the same row.
    target_id_or_slot: tuple[str, str, int] | None = None


KSEB_HISTORY = [
    {
        "role": "user",
        "content": "KSEB il register cheytha complaints kanikku",
    },
    {
        "role": "assistant",
        "content": (
            "Found 3 grievance records under KSEB.\n"
            "Retrieved grievance records: "
            + json.dumps(
                [
                    {
                        "grievance_id": "GRV-KSEB-0001",
                        "department_code": "KSEB",
                        "department_slot": 1,
                        "citizen_name": "Ramesh",
                        "status": "REGISTERED",
                    },
                    {
                        "grievance_id": "GRV-KSEB-0002",
                        "department_code": "KSEB",
                        "department_slot": 2,
                        "citizen_name": "Anitha",
                        "status": "IN_PROGRESS",
                    },
                    {
                        "grievance_id": "GRV-KSEB-0003",
                        "department_code": "KSEB",
                        "department_slot": 3,
                        "citizen_name": "Suresh",
                        "status": "REGISTERED",
                    },
                ],
                ensure_ascii=False,
            )
        ),
    },
]

MIXED_DEPARTMENT_HISTORY = [
    {
        "role": "user",
        "content": "Show all grievances across departments",
    },
    {
        "role": "assistant",
        "content": (
            "Found grievance records across departments.\n"
            "Retrieved grievance records: "
            + json.dumps(
                [
                    {
                        "grievance_id": "GRV-KSEB-0001",
                        "department_code": "KSEB",
                        "department_slot": 1,
                        "citizen_name": "Ramesh",
                        "status": "REGISTERED",
                    },
                    {
                        "grievance_id": "GRV-KWA-0001",
                        "department_code": "KWA",
                        "department_slot": 1,
                        "citizen_name": "Anitha",
                        "status": "IN_PROGRESS",
                    },
                    {
                        "grievance_id": "GRV-EDUCATION-0001",
                        "department_code": "EDUCATION",
                        "department_slot": 1,
                        "citizen_name": "Suresh",
                        "status": "REGISTERED",
                    },
                ],
                ensure_ascii=False,
            )
        ),
    },
]

SINGLE_RECORD_HISTORY = [
    {
        "role": "user",
        "content": "Show the KSEB grievance GRV-KSEB-0002",
    },
    {
        "role": "assistant",
        "content": (
            "Retrieved grievance GRV-KSEB-0002.\n"
            'Retrieved grievance records: '
            + json.dumps(
                {
                    "grievance_id": "GRV-KSEB-0002",
                    "department_code": "KSEB",
                    "department_slot": 2,
                    "citizen_name": "Anitha",
                    "status": "IN_PROGRESS",
                },
                ensure_ascii=False,
            )
        ),
    },
]


CASES: list[Case] = [
    # 1–10: English
    Case("English", "How many grievances are registered?", ("count",)),
    Case("English", "How many complaints are registered under KSEB?", ("count",), department="KSEB"),
    Case("English", "Show all grievances registered under KWA.", ("list",), department="KWA"),
    Case("English", "List all complaints from KSRTC.", ("list",), department="TRANSPORT"),
    Case("English", "Find the complaint filed by Ramesh.", ("search",), search_query="Ramesh"),
    Case("English", "Retrieve the complete details for GRV-KSEB-0001.", ("get_by_id",), grievance_id="GRV-KSEB-0001"),
    Case("English", "Show the details of KSEB slot 2.", ("get_by_slot",), department="KSEB", slot=2),
    Case("English", "Get the grievance in KSRTC slot number 4.", ("get_by_slot",), department="TRANSPORT", slot=4),
    Case("English", "How many grievances belong to the Social Justice Department?", ("count",), department="SOCIAL_JUSTICE"),
    Case("English", "Search for complaints submitted by Anitha.", ("search",), search_query="Anitha"),

    # 11–20: Malayalam script
    Case("Malayalam", "ആകെ എത്ര പരാതികൾ രജിസ്റ്റർ ചെയ്തിട്ടുണ്ട്?", ("count",)),
    Case("Malayalam", "കെഎസ്ഇബിയിൽ എത്ര പരാതികളുണ്ട്?", ("count",), department="KSEB"),
    Case("Malayalam", "കെഎസ്ഇബി വിഭാഗത്തിലെ പരാതികളുടെ പട്ടിക കാണിക്കുക", ("list",), department="KSEB"),
    Case("Malayalam", "കേരള ജല അതോറിറ്റിയിൽ രജിസ്റ്റർ ചെയ്ത പരാതികൾ കാണിക്കൂ", ("list",), department="KWA"),
    Case("Malayalam", "ഗതാഗത വകുപ്പിലെ പരാതികളുടെ എണ്ണം എത്ര?", ("count",), department="TRANSPORT"),
    Case("Malayalam", "രമേഷ് എന്ന വ്യക്തിയുടെ പരാതി കണ്ടെത്തുക", ("search",)),
    Case("Malayalam", "GRV-KSEB-0001 എന്ന പരാതിയുടെ പൂർണ്ണ വിവരങ്ങൾ നൽകുക", ("get_by_id",), grievance_id="GRV-KSEB-0001"),
    Case("Malayalam", "കെഎസ്ഇബിയിലെ രണ്ടാം സ്ലോട്ടിന്റെ വിശദാംശങ്ങൾ കാണിക്കുക", ("get_by_slot",), department="KSEB", slot=2),
    Case("Malayalam", "കെഎസ്ഇബിയിലെ മൂന്നാം സ്ലോട്ടിന്റെ വിവരങ്ങൾ വേണം", ("get_by_slot",), department="KSEB", slot=3),
    Case("Malayalam", "സാമൂഹ്യനീതി വകുപ്പിലെ പരാതികൾ പട്ടികപ്പെടുത്തുക", ("list",), department="SOCIAL_JUSTICE"),

    # 21–35: Manglish / Romanized Malayalam
    Case("Manglish", "ethra complaints register cheythittundu?", ("count",)),
    Case("Manglish", "KSEB yil ethra complaints undu?", ("count",), department="KSEB"),
    Case("Manglish", "KSEB il register cheytha complaints kanikku", ("list",), department="KSEB"),
    Case("Manglish", "KWA yile complaints ellam list cheyyu", ("list",), department="KWA"),
    Case("Manglish", "KSRTC yude complaints ethra undu?", ("count",), department="TRANSPORT"),
    Case("Manglish", "Ramesh inte complaint search cheyyu", ("search",), search_query="Ramesh"),
    Case("Manglish", "GRV-KSEB-0001 inte full details parayu", ("get_by_id",), grievance_id="GRV-KSEB-0001"),
    Case("Manglish", "KSEB le 3rd slot inte details venam", ("get_by_slot",), department="KSEB", slot=3),
    Case("Manglish", "KSEB le slot 3 inte details parayu", ("get_by_slot",), department="KSEB", slot=3),
    Case("Manglish", "KSEB slot number 3 details venam", ("get_by_slot",), department="KSEB", slot=3),
    Case("Manglish", "KSEB le moonam slot inte details venam", ("get_by_slot",), department="KSEB", slot=3),
    Case("Manglish", "KSEB il 2nd slot aaru register cheythu?", ("get_by_slot",), department="KSEB", slot=2),
    Case("Manglish", "Social justice department-il ethra complaints undu?", ("count",), department="SOCIAL_JUSTICE"),
    Case("Manglish", "PWD-yil complaints list cheyyu", ("list",), department="PWD"),
    Case("Manglish", "GRV-KWA-0001 inte status entha?", ("get_by_id",), grievance_id="GRV-KWA-0001"),

    # 36–40: Code-mixed English + Manglish
    Case("Code-mixed", "KSEB complaints count ethra?", ("count",), department="KSEB"),
    Case("Code-mixed", "Please KWA complaints list cheyyamo?", ("list",), department="KWA"),
    Case("Code-mixed", "GRV-KSEB-0002 details parayu please", ("get_by_id",), grievance_id="GRV-KSEB-0002"),
    Case("Code-mixed", "Anitha-yude complaint search cheyyu", ("search",), search_query="Anitha"),
    Case("Code-mixed", "TRANSPORT department-il total complaints ethra?", ("count",), department="TRANSPORT"),

    # 41–50: Contextual follow-ups
    Case("Follow-up", "third one inte full details venam", ("get_by_slot", "get_by_id"), target_id_or_slot=("GRV-KSEB-0003", "KSEB", 3), history=KSEB_HISTORY),
    Case("Follow-up", "second complaint inte full details parayu", ("get_by_slot", "get_by_id"), target_id_or_slot=("GRV-KSEB-0002", "KSEB", 2), history=KSEB_HISTORY),
    Case("Follow-up", "first one aaru submit cheythu?", ("get_by_id",), grievance_id="GRV-KSEB-0001", history=KSEB_HISTORY),
    Case("Follow-up", "aa complaint inte status entha?", ("get_by_id", "get_by_slot"), target_id_or_slot=("GRV-KSEB-0002", "KSEB", 2), history=SINGLE_RECORD_HISTORY),
    Case("Follow-up", "third oneinte summary parayamo?", ("get_by_slot", "get_by_id"), target_id_or_slot=("GRV-KSEB-0003", "KSEB", 3), history=KSEB_HISTORY),
    Case("Follow-up", "aa department-il ethra complaints undu?", ("count",), department="KSEB", history=KSEB_HISTORY),
    Case("Follow-up", "Anitha-yude full details venam", ("get_by_id",), grievance_id="GRV-KSEB-0002", history=KSEB_HISTORY),
    Case("Follow-up", "second one details venam", ("get_by_id", "get_by_slot"), target_id_or_slot=("GRV-KWA-0001", "KWA", 1), history=MIXED_DEPARTMENT_HISTORY),
    Case("Follow-up", "the third oneinte status entha?", ("get_by_id", "get_by_slot"), target_id_or_slot=("GRV-EDUCATION-0001", "EDUCATION", 1), history=MIXED_DEPARTMENT_HISTORY),
    Case("Follow-up", "athile first complaint eduthu kanikku", ("get_by_id", "get_by_slot"), target_id_or_slot=("GRV-KSEB-0001", "KSEB", 1), history=MIXED_DEPARTMENT_HISTORY),
]


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


def evaluate(case: Case, result: Any) -> tuple[bool, list[str]]:
    failures: list[str] = []
    action = str(getattr(result, "action", ""))
    department = getattr(result, "department_code", None)
    slot = getattr(result, "department_slot", None)
    grievance_id = getattr(result, "grievance_id", None)
    search_query = getattr(result, "search_query", None)

    if action not in case.expected_action:
        failures.append(f"action expected {case.expected_action}, got {action!r}")

    if case.department is not None and department != case.department:
        failures.append(f"department expected {case.department!r}, got {department!r}")

    if case.slot is not None and slot != case.slot:
        failures.append(f"slot expected {case.slot}, got {slot!r}")

    if case.grievance_id is not None and grievance_id != case.grievance_id:
        failures.append(f"grievance_id expected {case.grievance_id!r}, got {grievance_id!r}")

    if case.search_query is not None:
        if not search_query or normalize_text(case.search_query) not in normalize_text(search_query):
            failures.append(f"search_query expected to contain {case.search_query!r}, got {search_query!r}")

    if case.target_id_or_slot is not None:
        target_id, target_department, target_slot = case.target_id_or_slot
        id_match = action == "get_by_id" and grievance_id == target_id
        slot_match = (
            action == "get_by_slot"
            and department == target_department
            and slot == target_slot
        )
        if not (id_match or slot_match):
            failures.append(
                "target expected either "
                f"ID={target_id!r} or department={target_department!r}, slot={target_slot}; "
                f"got action={action!r}, department={department!r}, slot={slot!r}, ID={grievance_id!r}"
            )

    return not failures, failures


def main() -> int:
    print("=" * 76)
    print("OFFICIAL CHATBOT — 50-CASE INTENT / LANGUAGE BENCHMARK")
    print("Model:", __import__("official_assistant").OFFICIAL_MODEL)
    print("This benchmark calls the local intent model; it does not access SQLite.")
    print("=" * 76)

    category_totals: dict[str, int] = defaultdict(int)
    category_passes: dict[str, int] = defaultdict(int)
    failures: list[tuple[int, Case, list[str]]] = []
    started = time.time()

    for index, case in enumerate(CASES, start=1):
        category_totals[case.category] += 1
        try:
            result = understand_question(case.question, case.history)
            passed, problems = evaluate(case, result)
            if passed:
                category_passes[case.category] += 1
                marker = "PASS"
            else:
                failures.append((index, case, problems))
                marker = "FAIL"
            print(f"[{marker}] {index:02d}/50 [{case.category}] {case.question}")
            if not passed:
                for problem in problems:
                    print("       -", problem)
        except Exception as error:
            failures.append((index, case, [f"exception: {type(error).__name__}: {error}"]))
            print(f"[ERROR] {index:02d}/50 [{case.category}] {case.question}")
            print("       -", f"{type(error).__name__}: {error}")

    elapsed = time.time() - started
    passed_total = sum(category_passes.values())
    total = len(CASES)

    print("\n" + "=" * 76)
    print("CATEGORY RESULTS")
    for category in ("English", "Malayalam", "Manglish", "Code-mixed", "Follow-up"):
        count = category_totals[category]
        passed = category_passes[category]
        percentage = (passed / count * 100) if count else 0.0
        print(f"{category:12s}: {passed:2d}/{count:2d} ({percentage:5.1f}%)")

    percentage = passed_total / total * 100
    print("-" * 76)
    print(f"OVERALL      : {passed_total:2d}/{total:2d} ({percentage:5.1f}%)")
    print(f"Elapsed      : {elapsed:.1f} seconds")

    if failures:
        print("\nFAILED CASES TO REVIEW:")
        for index, case, problems in failures:
            print(f"\n{index:02d}. [{case.category}] {case.question}")
            for problem in problems:
                print("   -", problem)
    else:
        print("\nAll benchmark cases passed.")

    print("\nNote: This is a fixed, hand-authored benchmark, not a statistical")
    print("guarantee of 99% accuracy on unseen real-world questions.")

    return 0 if not failures else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nBenchmark interrupted.")
        raise SystemExit(130)
