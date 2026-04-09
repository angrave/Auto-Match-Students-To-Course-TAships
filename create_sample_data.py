#!/usr/bin/env python3
"""Create sample student.xlsx and courses.xlsx for testing."""
import pandas as pd

students = pd.DataFrame({
    "studentid":          ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank"],
    "preferredcourse":    ["CS101, CS201", "CS201, CS101", "CS101", "CS301, CS201", "CS201, CS301", "CS101, CS301"],
    "nonpreferredcourse": ["CS301", "CS301", "", "CS101", "", "CS201"],
})
students.to_excel("student.xlsx", index=False)

courses = pd.DataFrame({
    "course":              ["CS101", "CS201", "CS301"],
    "numbertaslots":       [2, 2, 1],
    "preferredstudents":   ["Alice, Frank, Carol", "Bob, Eve", "Dave"],
    "nonpreferredstudents":["Dave", "Dave, Frank", ""],
})
courses.to_excel("courses.xlsx", index=False)

print("Created student.xlsx and courses.xlsx")
