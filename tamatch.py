#!/usr/bin/env python3
"""
Stable marriage algorithm to match grad students to TA slots.

Input:  student.xlsx  - columns: studentid, preferredcourse, nonpreferredcourse
        courses.xlsx  - columns: course, numbertaslots, preferredstudents, nonpreferredstudents

Output: draftmatch.xlsx - columns: student, course, combinedscore

Scoring: preferred items scored from 100 down to 1 by rank,
         nonpreferred items scored from -100 up to -1 by rank,
         unmentioned = 0. Combined score = student_pref + course_pref.
"""

import sys
import re
import pandas as pd
from collections import defaultdict

USAGE = """\
Usage: python3 tamatch.py [student.xlsx courses.xlsx output.xlsx]

  0 args: reads student.xlsx & courses.xlsx, writes draftmatch.xlsx
  3 args: reads <student> & <courses>, writes <output>
"""


def parse_list(value):
    """Parse a comma/whitespace separated string into a list of trimmed tokens."""
    if pd.isna(value) or str(value).strip() == "":
        return []
    return [x.strip() for x in re.split(r"[,\s]+", str(value).strip()) if x.strip()]


def compute_scores(preferred, nonpreferred):
    """Return a dict of item -> score.

    Preferred rank 1 gets 100, rank N gets max(1, ...) — evenly spaced.
    Nonpreferred rank 1 gets -100, rank N gets min(-1, ...).
    """
    scores = {}
    n = len(preferred)
    for i, item in enumerate(preferred):
        # rank 0 (best) -> 100, last -> max(1, ...)
        scores[item] = round(100 - i * (99 / max(n - 1, 1))) if n > 1 else 100

    n = len(nonpreferred)
    for i, item in enumerate(nonpreferred):
        # rank 0 (worst) -> -100, last -> min(-1, ...)
        scores[item] = round(-100 + i * (99 / max(n - 1, 1))) if n > 1 else -100

    return scores


def load_students(path="student.xlsx"):
    df = pd.read_excel(path)
    df.columns = [c.strip().lower() for c in df.columns]
    students = {}
    for _, row in df.iterrows():
        sid = str(row["studentid"]).strip()
        pref = parse_list(row.get("preferredcourse", ""))
        nonpref = parse_list(row.get("nonpreferredcourse", ""))
        students[sid] = compute_scores(pref, nonpref)
    return students


def load_courses(path="courses.xlsx"):
    df = pd.read_excel(path)
    df.columns = [c.strip().lower() for c in df.columns]
    courses = {}
    for _, row in df.iterrows():
        cname = str(row["course"]).strip()
        slots = int(row["numbertaslots"])
        pref = parse_list(row.get("preferredstudents", ""))
        nonpref = parse_list(row.get("nonpreferredstudents", ""))
        courses[cname] = {"slots": slots, "scores": compute_scores(pref, nonpref)}
    return courses


def combined_score(student_id, course_name, student_prefs, course_data):
    """Combined score = student's feeling about course + course's feeling about student."""
    s_score = student_prefs.get(student_id, {}).get(course_name, 0)
    c_score = course_data.get(course_name, {}).get("scores", {}).get(student_id, 0)
    return s_score + c_score


def stable_match(student_prefs, course_data):
    """Hospital-resident style Gale-Shapley (student-proposing).

    Each student proposes to courses in order of their combined score (descending).
    Courses accept up to their slot count, replacing the worst current match if
    the new proposal is better.
    """
    all_courses = list(course_data.keys())

    # Build each student's full ranked proposal list (all courses, sorted by combined score desc)
    proposal_lists = {}
    for sid in student_prefs:
        ranked = sorted(
            all_courses,
            key=lambda c: combined_score(sid, c, student_prefs, course_data),
            reverse=True,
        )
        proposal_lists[sid] = list(ranked)

    # Current assignments: course -> list of (combined_score, student_id)
    assignments = defaultdict(list)
    free_students = list(student_prefs.keys())
    proposal_index = {sid: 0 for sid in student_prefs}  # next course to propose to

    while free_students:
        sid = free_students.pop(0)
        idx = proposal_index[sid]

        if idx >= len(all_courses):
            # Exhausted all courses — will go to CS00
            continue

        course = proposal_lists[sid][idx]
        proposal_index[sid] = idx + 1
        score = combined_score(sid, course, student_prefs, course_data)
        slots = course_data[course]["slots"]

        if len(assignments[course]) < slots:
            assignments[course].append((score, sid))
        else:
            # Find worst currently matched student in this course
            assignments[course].sort()
            worst_score, worst_sid = assignments[course][0]
            if score > worst_score:
                assignments[course][0] = (score, sid)
                free_students.append(worst_sid)  # worst is now free
            else:
                free_students.append(sid)  # rejected, try next course

    return assignments


def find_warnings(student_path, course_path):
    """Check for references to nonexistent student IDs or course names."""
    sdf = pd.read_excel(student_path)
    sdf.columns = [c.strip().lower() for c in sdf.columns]
    cdf = pd.read_excel(course_path)
    cdf.columns = [c.strip().lower() for c in cdf.columns]

    student_ids = {str(row["studentid"]).strip() for _, row in sdf.iterrows() if str(row["studentid"]).strip()}
    course_names = {str(row["course"]).strip() for _, row in cdf.iterrows() if str(row["course"]).strip()}

    warnings = []
    for _, row in sdf.iterrows():
        sid = str(row["studentid"]).strip()
        if not sid:
            continue
        for c in parse_list(row.get("preferredcourse", "")) + parse_list(row.get("nonpreferredcourse", "")):
            if c not in course_names:
                warnings.append(f"Student {sid} mentioned nonexistent course {c}")

    for _, row in cdf.iterrows():
        cn = str(row["course"]).strip()
        if not cn:
            continue
        for s in parse_list(row.get("preferredstudents", "")) + parse_list(row.get("nonpreferredstudents", "")):
            if s not in student_ids:
                warnings.append(f"Course {cn} mentioned nonexistent student {s}")

    return warnings


def build_output(student_prefs, course_data, assignments):
    """Build the output rows from assignments."""
    matched = set()
    rows = []
    for course, pairs in assignments.items():
        for score, sid in sorted(pairs, key=lambda x: -x[0]):
            rows.append({"student": sid, "course": course, "combinedscore": score})
            matched.add(sid)

    # Unmatched students -> CS00
    for sid in student_prefs:
        if sid not in matched:
            score = combined_score(sid, "CS00", student_prefs, course_data)
            rows.append({"student": sid, "course": "CS00", "combinedscore": score})

    # Unfilled slots -> 'todo'
    for course, cdata in course_data.items():
        filled = len(assignments.get(course, []))
        for _ in range(cdata["slots"] - filled):
            rows.append({"student": "todo", "course": course, "combinedscore": 0})

    return rows


def main():
    args = sys.argv[1:]
    if len(args) == 0:
        student_path, course_path, output_path = "student.xlsx", "courses.xlsx", "draftmatch.xlsx"
    elif len(args) == 3:
        student_path, course_path, output_path = args
    else:
        print(USAGE, file=sys.stderr)
        sys.exit(1)

    warnings = find_warnings(student_path, course_path)
    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for w in warnings:
            print(f"  {w}")
        print()

    student_prefs = load_students(student_path)
    course_data = load_courses(course_path)
    assignments = stable_match(student_prefs, course_data)
    rows = build_output(student_prefs, course_data, assignments)

    df = pd.DataFrame(rows, columns=["student", "course", "combinedscore"])
    df.to_excel(output_path, index=False)
    print(f"Wrote {output_path} with {len(df)} rows")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
