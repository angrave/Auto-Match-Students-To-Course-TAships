#!/usr/bin/env python3
"""Generate all test input xlsx files and expected output xlsx files."""
import pandas as pd
import os

def write(name, students_df, courses_df, expected_df):
    d = os.path.dirname(__file__)
    students_df.to_excel(os.path.join(d, f"{name}_student.xlsx"), index=False)
    courses_df.to_excel(os.path.join(d, f"{name}_courses.xlsx"), index=False)
    expected_df.to_excel(os.path.join(d, f"{name}_expected.xlsx"), index=False)
    print(f"  {name}")


# ── Test 1: one_to_one ──────────────────────────────────────────────
# 1 student, 1 course, 1 slot — simplest possible case
write("t01_one_to_one",
    pd.DataFrame({
        "studentid": ["Alice"],
        "preferredcourse": ["CS101"],
        "nonpreferredcourse": [""],
    }),
    pd.DataFrame({
        "course": ["CS101"],
        "numbertaslots": [1],
        "preferredstudents": ["Alice"],
        "nonpreferredstudents": [""],
    }),
    pd.DataFrame({
        "student": ["Alice"],
        "course": ["CS101"],
        "combinedscore": [200],  # 100 + 100
    }),
)

# ── Test 2: perfect_match ───────────────────────────────────────────
# 2 students, 2 courses with 1 slot each, mutual first choices
write("t02_perfect_match",
    pd.DataFrame({
        "studentid": ["Alice", "Bob"],
        "preferredcourse": ["CS101", "CS201"],
        "nonpreferredcourse": ["", ""],
    }),
    pd.DataFrame({
        "course": ["CS101", "CS201"],
        "numbertaslots": [1, 1],
        "preferredstudents": ["Alice", "Bob"],
        "nonpreferredstudents": ["", ""],
    }),
    pd.DataFrame({
        "student": ["Alice", "Bob"],
        "course": ["CS101", "CS201"],
        "combinedscore": [200, 200],
    }),
)

# ── Test 3: surplus_students ────────────────────────────────────────
# 3 students, 1 course, 1 slot — 2 go to CS00
write("t03_surplus_students",
    pd.DataFrame({
        "studentid": ["Alice", "Bob", "Carol"],
        "preferredcourse": ["CS101", "CS101", "CS101"],
        "nonpreferredcourse": ["", "", ""],
    }),
    pd.DataFrame({
        "course": ["CS101"],
        "numbertaslots": [1],
        "preferredstudents": ["Alice"],
        "nonpreferredstudents": [""],
    }),
    pd.DataFrame({
        "student": ["Alice", "Bob", "Carol"],
        "course": ["CS101", "CS00", "CS00"],
        "combinedscore": [200, 0, 0],  # Alice: 100+100; others unmatched, CS00 score=0
    }),
)

# ── Test 4: surplus_slots ───────────────────────────────────────────
# 1 student, 1 course with 3 slots — 2 unfilled
write("t04_surplus_slots",
    pd.DataFrame({
        "studentid": ["Alice"],
        "preferredcourse": ["CS101"],
        "nonpreferredcourse": [""],
    }),
    pd.DataFrame({
        "course": ["CS101"],
        "numbertaslots": [3],
        "preferredstudents": ["Alice"],
        "nonpreferredstudents": [""],
    }),
    pd.DataFrame({
        "student": ["Alice", "todo", "todo"],
        "course": ["CS101", "CS101", "CS101"],
        "combinedscore": [200, 0, 0],
    }),
)

# ── Test 5: competing_preferences ───────────────────────────────────
# Both students prefer CS101, but CS101 only has 1 slot and prefers Bob.
# Alice gets displaced to CS201.
write("t05_competing",
    pd.DataFrame({
        "studentid": ["Alice", "Bob"],
        "preferredcourse": ["CS101", "CS101"],
        "nonpreferredcourse": ["", ""],
    }),
    pd.DataFrame({
        "course": ["CS101", "CS201"],
        "numbertaslots": [1, 1],
        "preferredstudents": ["Bob", ""],
        "nonpreferredstudents": ["", ""],
    }),
    pd.DataFrame({
        # Bob gets CS101 (100+100=200), Alice ends up at CS201 (0+0=0)
        "student": ["Bob", "Alice"],
        "course": ["CS101", "CS201"],
        "combinedscore": [200, 0],
    }),
)

# ── Test 6: nonpreferred_avoidance ──────────────────────────────────
# Alice marks CS201 as nonpreferred. Course CS201 also marks Alice as nonpreferred.
# Alice should end up at CS101 despite no explicit preference for it.
write("t06_nonpreferred",
    pd.DataFrame({
        "studentid": ["Alice"],
        "preferredcourse": [""],
        "nonpreferredcourse": ["CS201"],
    }),
    pd.DataFrame({
        "course": ["CS101", "CS201"],
        "numbertaslots": [1, 1],
        "preferredstudents": ["", ""],
        "nonpreferredstudents": ["", "Alice"],
    }),
    pd.DataFrame({
        # CS101 combined=0+0=0, CS201 combined=(-100)+(-100)=-200
        # Alice proposes to CS101 first (higher score)
        "student": ["Alice", "todo"],
        "course": ["CS101", "CS201"],
        "combinedscore": [0, 0],
    }),
)

# ── Test 7: no_preferences ─────────────────────────────────────────
# Everyone has empty preferences — all scores are 0
write("t07_no_prefs",
    pd.DataFrame({
        "studentid": ["Alice", "Bob"],
        "preferredcourse": ["", ""],
        "nonpreferredcourse": ["", ""],
    }),
    pd.DataFrame({
        "course": ["CS101", "CS201"],
        "numbertaslots": [1, 1],
        "preferredstudents": ["", ""],
        "nonpreferredstudents": ["", ""],
    }),
    pd.DataFrame({
        # All combined scores 0; both get placed (order depends on iteration)
        "student": ["Alice", "Bob"],
        "course": ["CS101", "CS201"],
        "combinedscore": [0, 0],
    }),
)

# ── Test 8: multi_slot_course ───────────────────────────────────────
# One course with 3 slots, 3 students, all prefer it
write("t08_multi_slot",
    pd.DataFrame({
        "studentid": ["Alice", "Bob", "Carol"],
        "preferredcourse": ["CS101", "CS101", "CS101"],
        "nonpreferredcourse": ["", "", ""],
    }),
    pd.DataFrame({
        "course": ["CS101"],
        "numbertaslots": [3],
        "preferredstudents": ["Alice, Bob, Carol"],
        "nonpreferredstudents": [""],
    }),
    pd.DataFrame({
        # Alice: 100+100=200, Bob: 100+50=150, Carol: 100+1=101
        "student": ["Alice", "Bob", "Carol"],
        "course": ["CS101", "CS101", "CS101"],
        "combinedscore": [200, 150, 101],
    }),
)

# ── Test 9: displacement_chain ──────────────────────────────────────
# A→CS101, B→CS101, C→CS201. CS101 has 1 slot, prefers B.
# A proposes CS101, gets in. B proposes CS101, displaces A. A goes to CS201, displaces C?
# CS201 has 1 slot. C has nowhere else → CS00.
write("t09_displacement",
    pd.DataFrame({
        "studentid": ["Alice", "Bob", "Carol"],
        "preferredcourse": ["CS101", "CS101", "CS201"],
        "nonpreferredcourse": ["", "", ""],
    }),
    pd.DataFrame({
        "course": ["CS101", "CS201"],
        "numbertaslots": [1, 1],
        "preferredstudents": ["Bob", "Carol"],
        "nonpreferredstudents": ["", ""],
    }),
    pd.DataFrame({
        # Bob: CS101 (100+100=200), Carol: CS201 (100+100=200)
        # Alice displaced from CS101, proposes CS201 (0+0=0), Carol has 200 > 0, Alice rejected
        # Alice → CS00
        "student": ["Bob", "Carol", "Alice"],
        "course": ["CS101", "CS201", "CS00"],
        "combinedscore": [200, 200, 0],
    }),
)

# ── Test 10: ranked_preferences ─────────────────────────────────────
# Test that rank ordering within preferences works correctly
# Alice prefers CS101 > CS201 > CS301 (scores 100, 50, 1)
# All courses have 1 slot and prefer Alice
write("t10_ranked",
    pd.DataFrame({
        "studentid": ["Alice"],
        "preferredcourse": ["CS101, CS201, CS301"],
        "nonpreferredcourse": [""],
    }),
    pd.DataFrame({
        "course": ["CS101", "CS201", "CS301"],
        "numbertaslots": [1, 1, 1],
        "preferredstudents": ["Alice", "Alice", "Alice"],
        "nonpreferredstudents": ["", "", ""],
    }),
    pd.DataFrame({
        # Alice gets CS101 (100+100=200), rest are todo
        "student": ["Alice", "todo", "todo"],
        "course": ["CS101", "CS201", "CS301"],
        "combinedscore": [200, 0, 0],
    }),
)

# ── Test 11: whitespace_and_comma_parsing ───────────────────────────
# Preferences use mixed separators (commas, spaces, both)
write("t11_parsing",
    pd.DataFrame({
        "studentid": ["Alice", "Bob"],
        "preferredcourse": ["CS101,CS201", "CS201  CS101"],  # comma vs spaces
        "nonpreferredcourse": ["", ""],
    }),
    pd.DataFrame({
        "course": ["CS101", "CS201"],
        "numbertaslots": [1, 1],
        "preferredstudents": ["Alice,  Bob", "Bob , Alice"],  # mixed comma+space
        "nonpreferredstudents": ["", ""],
    }),
    pd.DataFrame({
        # Alice: CS101 combined=100+100=200, CS201 combined=50+50=150
        # Bob:   CS201 combined=100+100=200, CS101 combined=50+50=100
        # Both get their top choice
        "student": ["Alice", "Bob"],
        "course": ["CS101", "CS201"],
        "combinedscore": [200, 200],
    }),
)

# ── Test 12: mutual_nonpreferred ────────────────────────────────────
# Student and course mutually dislike each other, but it's the only option
write("t12_mutual_dislike",
    pd.DataFrame({
        "studentid": ["Alice"],
        "preferredcourse": [""],
        "nonpreferredcourse": ["CS101"],
    }),
    pd.DataFrame({
        "course": ["CS101"],
        "numbertaslots": [1],
        "preferredstudents": [""],
        "nonpreferredstudents": ["Alice"],
    }),
    pd.DataFrame({
        # Only option, combined = -100 + -100 = -200
        "student": ["Alice"],
        "course": ["CS101"],
        "combinedscore": [-200],
    }),
)

# ── Test 13: whitespace_trimming ────────────────────────────────────
# IDs with leading/trailing spaces should be trimmed and still match
write("t13_trimming",
    pd.DataFrame({
        "studentid": ["  Alice  ", "Bob "],
        "preferredcourse": [" CS101 ", "CS201"],
        "nonpreferredcourse": ["", ""],
    }),
    pd.DataFrame({
        "course": [" CS101", "CS201 "],
        "numbertaslots": [1, 1],
        "preferredstudents": ["Alice ", " Bob"],
        "nonpreferredstudents": ["", ""],
    }),
    pd.DataFrame({
        "student": ["Alice", "Bob"],
        "course": ["CS101", "CS201"],
        "combinedscore": [200, 200],
    }),
)

# ── Test 14: bad_references ─────────────────────────────────────────
# Student mentions nonexistent course, course mentions nonexistent student.
# Matching should still work; warnings are informational only.
write("t14_bad_refs",
    pd.DataFrame({
        "studentid": ["Alice"],
        "preferredcourse": ["CS101, CS999"],  # CS999 doesn't exist
        "nonpreferredcourse": [""],
    }),
    pd.DataFrame({
        "course": ["CS101"],
        "numbertaslots": [1],
        "preferredstudents": ["Alice, Zed"],  # Zed doesn't exist
        "nonpreferredstudents": [""],
    }),
    pd.DataFrame({
        # Alice still matches CS101 fine
        "student": ["Alice"],
        "course": ["CS101"],
        "combinedscore": [200],  # 100 (student pref rank 1) + 100 (course pref rank 1)
    }),
)

print("All test data created.")
