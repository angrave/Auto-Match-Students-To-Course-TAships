#!/usr/bin/env python3
"""Generate realistic demo data for tamatch.py stable marriage TA matching."""

import pandas as pd
import random
import string

# --- Course definitions (40 total) ---
courses_100 = ['cs101', 'cs105', 'cs124', 'cs125', 'cs128']           # 5 courses, 10 TAs each
courses_200 = ['cs173', 'cs211', 'cs225', 'cs233', 'cs241', 'cs374']  # 6 courses,  6 TAs each
courses_400 = [                                                         # 17 courses, 1 TA each
    'cs411', 'cs421', 'cs425', 'cs427', 'cs428',
    'cs431', 'cs433', 'cs438', 'cs446', 'cs461',
    'cs466', 'cs473', 'cs476', 'cs484', 'cs491',
    'cs498abd', 'cs498rk2',                        # 498 special topics need section codes
]
courses_500 = [                                                         # 12 courses, 1 TA each
    'cs510', 'cs523', 'cs525', 'cs526', 'cs533',
    'cs546', 'cs547', 'cs554', 'cs556', 'cs576',
    'cs583', 'cs591',
]

all_courses = courses_100 + courses_200 + courses_400 + courses_500
assert len(all_courses) == 40, f"Expected 40 courses, got {len(all_courses)}"

slots = {}
for c in courses_100: slots[c] = 10
for c in courses_200: slots[c] = 6
for c in courses_400: slots[c] = 1
for c in courses_500: slots[c] = 1

total_slots = sum(slots.values())
print(f"Courses: {len(all_courses)}, Total TA slots: {total_slots}")

# --- Student IDs: 6 lowercase letters + 1 digit ---
def gen_student_ids(n, seed=42):
    rng = random.Random(seed)
    ids, seen = [], set()
    while len(ids) < n:
        letters = ''.join(rng.choices(string.ascii_lowercase, k=6))
        digit = str(rng.randint(0, 9))
        sid = letters + digit
        if sid not in seen:
            seen.add(sid)
            ids.append(sid)
    return ids

NUM_STUDENTS = 100   # fewer than 115 slots → some "todo" unfilled slots
student_ids = gen_student_ids(NUM_STUDENTS)

# --- Interest groups: realistic course clusters ---
systems   = ['cs233', 'cs241', 'cs431', 'cs433', 'cs438', 'cs461', 'cs525', 'cs526']
ml_ai     = ['cs446', 'cs484', 'cs498abd', 'cs547', 'cs583', 'cs498rk2']
theory    = ['cs173', 'cs374', 'cs421', 'cs473', 'cs476', 'cs510', 'cs523']
intro_ta  = ['cs101', 'cs105', 'cs124', 'cs125', 'cs128', 'cs211', 'cs225']
db_se     = ['cs411', 'cs425', 'cs427', 'cs428', 'cs466', 'cs546', 'cs591']
pl_comp   = ['cs421', 'cs427', 'cs476', 'cs510', 'cs533', 'cs576']
graphics  = ['cs428', 'cs466', 'cs491', 'cs554', 'cs498rk2']
security  = ['cs427', 'cs461', 'cs526', 'cs533']
hci_net   = ['cs411', 'cs466', 'cs538', 'cs556', 'cs563']  # some don't exist → realistic typo risk avoided

# Assign students to groups
rng = random.Random(7)
group_defs = [
    (systems,  20),
    (ml_ai,    18),
    (theory,   15),
    (intro_ta, 17),
    (db_se,    13),
    (pl_comp,   8),
    (graphics,  5),
    (security,  4),
]
group_assignments = []
idx = 0
for group_courses, count in group_defs:
    for _ in range(count):
        if idx < NUM_STUDENTS:
            group_assignments.append((student_ids[idx], group_courses))
            idx += 1

# Remaining students get a mixed random set
for sid in student_ids[idx:]:
    mixed = rng.sample(all_courses, 4)
    group_assignments.append((sid, mixed))

# --- Build student preference rows ---
rng2 = random.Random(101)
student_rows = []
for sid, group_courses in group_assignments:
    # 2-4 preferred courses from their interest area
    num_pref = rng2.randint(2, min(4, len(group_courses)))
    preferred = rng2.sample(group_courses, num_pref)

    # 30% chance: also add one course from outside their group (broadens experience)
    if rng2.random() < 0.30:
        outside = [c for c in all_courses if c not in preferred]
        preferred.append(rng2.choice(outside))

    # 35% chance: 1-2 non-preferred courses (courses they really don't want)
    nonpreferred = []
    if rng2.random() < 0.35:
        candidates = [c for c in all_courses if c not in preferred]
        nonpreferred = rng2.sample(candidates, rng2.randint(1, 2))

    student_rows.append({
        'studentid': sid,
        'preferredcourse': ', '.join(preferred),
        'nonpreferredcourse': ', '.join(nonpreferred),
    })

# --- Build course → applicant maps ---
course_applicants  = {c: [] for c in all_courses}
course_avoiders    = {c: [] for c in all_courses}

for row in student_rows:
    sid = row['studentid']
    for token in [t.strip() for t in row['preferredcourse'].split(',') if t.strip()]:
        if token in course_applicants:
            course_applicants[token].append(sid)
    for token in [t.strip() for t in row['nonpreferredcourse'].split(',') if t.strip()]:
        if token in course_avoiders:
            course_avoiders[token].append(sid)

# --- Build course preference rows ---
rng3 = random.Random(202)
course_rows = []
for c in all_courses:
    applicants = list(course_applicants[c])
    avoiders   = list(course_avoiders[c])
    n_slots    = slots[c]

    # Instructors prefer some applicants; when oversubscribed they rank them
    if len(applicants) > n_slots:
        # Instructor has a ranked shortlist (slightly more than slots)
        shortlist_size = min(len(applicants), n_slots + rng3.randint(1, 3))
        rng3.shuffle(applicants)
        preferred_students = applicants[:shortlist_size]
    elif applicants:
        # All applicants welcome; shuffle to give ranked ordering
        rng3.shuffle(applicants)
        preferred_students = applicants
        # 25% chance instructor also proactively names a known student
        if rng3.random() < 0.25:
            extras = [s for s in student_ids if s not in preferred_students]
            if extras:
                preferred_students.append(rng3.choice(extras))
    else:
        # No applicants; instructor may name a student they know
        preferred_students = []
        if rng3.random() < 0.20:
            preferred_students = rng3.sample(student_ids, rng3.randint(1, 2))

    # Non-preferred: 40% chance to flag a mutual-avoider; 8% chance random student
    nonpreferred_students = []
    if avoiders and rng3.random() < 0.40:
        nonpreferred_students = rng3.sample(avoiders, min(len(avoiders), rng3.randint(1, 2)))
    elif rng3.random() < 0.08:
        others = [s for s in student_ids if s not in preferred_students]
        if others:
            nonpreferred_students = [rng3.choice(others)]

    course_rows.append({
        'course':               c,
        'numbertaslots':        n_slots,
        'preferredstudents':    ', '.join(preferred_students),
        'nonpreferredstudents': ', '.join(nonpreferred_students),
    })

# --- Write Excel files ---
df_students = pd.DataFrame(student_rows, columns=['studentid', 'preferredcourse', 'nonpreferredcourse'])
df_courses  = pd.DataFrame(course_rows,  columns=['course', 'numbertaslots', 'preferredstudents', 'nonpreferredstudents'])

df_students.to_excel('demo-student.xlsx', index=False)
df_courses.to_excel('demo-courses.xlsx',  index=False)

print(f"Wrote demo-student.xlsx  ({len(df_students)} students)")
print(f"Wrote demo-courses.xlsx  ({len(df_courses)} courses)")
print()

# Sanity summary
pref_counts  = df_students['preferredcourse'].apply(lambda x: len([t for t in x.split(',') if t.strip()]))
npref_counts = df_students['nonpreferredcourse'].apply(lambda x: len([t for t in x.split(',') if t.strip()]))
print(f"Students with >=1 preferred course:     {(pref_counts  >= 1).sum()}")
print(f"Students with >=1 nonpreferred course:  {(npref_counts >= 1).sum()}")

cp = df_courses['preferredstudents'].apply(lambda x: len([t for t in x.split(',') if t.strip()]))
cn = df_courses['nonpreferredstudents'].apply(lambda x: len([t for t in x.split(',') if t.strip()]))
print(f"Courses with >=1 preferred student:     {(cp >= 1).sum()}")
print(f"Courses with >=1 nonpreferred student:  {(cn >= 1).sum()}")
print()
print("Course slot breakdown:")
for level, lst in [('100-level', courses_100), ('200-level', courses_200),
                   ('400-level / 498', courses_400), ('500-level', courses_500)]:
    total = sum(slots[c] for c in lst)
    print(f"  {level}: {len(lst)} courses, {total} total slots")
print(f"  TOTAL: {len(all_courses)} courses, {total_slots} slots for {NUM_STUDENTS} students")
