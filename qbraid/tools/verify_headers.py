# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Script to verify qBraid copyright file headers

"""
import os
import re

header = """# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
# 
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.
"""

skip_files = [
    "qbraid/api/retry.py",
    "qbraid/transpiler/cirq_braket/convert_from_braket.py",
    "qbraid/transpiler/cirq_braket/convert_to_braket.py",
    "qbraid/transpiler/cirq_braket/tests/test_from_braket.py",
    "qbraid/transpiler/cirq_braket/tests/test_to_braket.py",
    "qbraid/transpiler/cirq_qasm/qasm_parser.py",
    "qbraid/transpiler/cirq_qasm/tests/test_qasm_parser.py",
]


def header_exists(file_path):
    with open(file_path, "r", encoding="ISO-8859-1") as f:
        content = f.read()
    return content.startswith(header)


def should_skip(file_path):
    rel_path = os.path.relpath(file_path, project_directory)
    rel_path = re.sub(r"^qbraid[/\\]", "", rel_path)

    if rel_path in skip_files:
        return True

    if os.path.basename(file_path) == "__init__.py":
        with open(file_path, "r", encoding="ISO-8859-1") as f:
            content = f.read()
        return not content.strip()

    return False


def replace_or_add_header(file_path):
    if should_skip(file_path):
        return

    with open(file_path, "r", encoding="ISO-8859-1") as f:
        content = f.read()

    if header_exists(file_path):
        return

    lines = content.splitlines()

    comment_lines = []
    first_skipped_line = None
    for index, line in enumerate(lines):
        if line.startswith("#"):
            comment_lines.append(line)
        else:
            first_skipped_line = index
            break

    new_content_lines = [header.rstrip("\r\n")] + lines[first_skipped_line:]
    new_content = "\n".join(new_content_lines)

    with open(file_path, "w", encoding="ISO-8859-1") as f:
        f.write(new_content)


def process_files_in_directory(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                replace_or_add_header(file_path)


if __name__ == "__main__":
    script_directory = os.path.dirname(os.path.abspath(__file__))
    project_directory = os.path.abspath(os.path.join(script_directory, ".."))
    process_files_in_directory(project_directory)
    print(
        "Header added or replaced in all .py files in the specified directory and sub-directories, if applicable."
    )
