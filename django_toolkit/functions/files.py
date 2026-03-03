import os
from typing import Literal
from pathlib import Path


def get_project_name():
    settings_module = os.environ.get("DJANGO_SETTINGS_MODULE")
    if settings_module:
        return settings_module.split(".")[0]
    return ""


def is_in_file(filename, string):
    """check if string is in file, returns True or False"""
    with open(filename, "r") as file:
        lines = file.readlines()

    for line in lines:
        # spacial case ''
        if string == '""' and '""' in line:
            return True
        elif string == "''" and "''" in line:
            return True
        elif string in line:
            return True

    return False


def insert_line_in_file(
    file_path: str | Path,
    anchor: str,
    line_to_insert: str,
    position: Literal["before", "after"] = "after",
    check_string: str | None = None,
) -> str | bool:
    """
    Insert a single line in a file relative to an anchor string.

    If `check_string` exists in the file, insertion is skipped.
    If `check_string` is not provided, `line_to_insert` is used for the existence check.

    Returns:
        The path of the modified file if a line was inserted, or False if no changes were made.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        return False

    # Read file content
    content = file_path.read_text(encoding="utf-8")

    string_to_check = check_string if check_string is not None else line_to_insert
    if string_to_check != "" and string_to_check in content:
        return False

    # Check if anchor exists
    if anchor not in content:
        return False

    # Split into lines
    lines = content.split("\n")

    # Find anchor line
    if "\n" in anchor:
        anchor_start_index = content.find(anchor)
        if anchor_start_index == -1:
            return False

        anchor_start_line = content[:anchor_start_index].count("\n")
        anchor_line_count = anchor.count("\n") + 1
        insert_index = (
            anchor_start_line
            if position == "before"
            else anchor_start_line + anchor_line_count
        )

        lines.insert(insert_index, line_to_insert)

        # Write back
        file_path.write_text("\n".join(lines), encoding="utf-8")
        return file_path.as_posix()

    for i, line in enumerate(lines):
        if anchor in line:
            # Insert before or after
            insert_index = i if position == "before" else i + 1

            lines.insert(insert_index, line_to_insert)

            # Write back
            file_path.write_text("\n".join(lines), encoding="utf-8")
            return file_path.as_posix()

    return False


def insert_lines_in_file(
    file_path: str | Path,
    anchor: str,
    lines_to_insert: list[str],
    position: Literal["before", "after"] = "after",
    check_as_block: bool = False,
    skip_if_any_exists: bool = False,
) -> str | bool:
    """
    Insert multiple lines in a file relative to an anchor string.

    `insert_line_in_file` performs the actual insertion. This function handles
    multi-line checks and insertion order.

    Returns:
        The path of the modified file if lines were inserted, or False if no changes were made.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return False

    if not lines_to_insert:
        return False

    content = file_path.read_text(encoding="utf-8")

    if check_as_block:
        block_to_check = "\n".join(lines_to_insert)
        if block_to_check in content:
            return False
        lines_for_insert = lines_to_insert
    else:
        if skip_if_any_exists and any(line in content for line in lines_to_insert):
            return False
        lines_for_insert = [line for line in lines_to_insert if line not in content]
        if not lines_for_insert:
            return False

    if position == "after":
        ordered_lines = list(reversed(lines_for_insert))
    else:
        ordered_lines = lines_for_insert

    modified_path: str | bool = False
    for line_to_insert in ordered_lines:
        file = insert_line_in_file(
            file_path=file_path,
            anchor=anchor,
            line_to_insert=line_to_insert,
            position=position,
            check_string=line_to_insert,
        )
        if file:
            modified_path = file

    return modified_path


def create_file(
    file_path: str | Path,
    content: str = "",
    overwrite: bool = False,
    create_dirs: bool = True,
) -> str | bool:
    """
        Create a file with optional content.

        Args:
            file_path: Path to the file to create
            content: Content to write to the file (default: empty string)
            overwrite: If True, overwrite existing file. If False, skip if exists (default: False)
            create_dirs: If True, create parent directories if they don't exist (default: True)

        Returns:
            The path of the created/written file if successful, or False if the file already exists and overwrite=False

        Example:
            # Create empty file
            create_file('app/urls.py')

            # Create file with content
            create_file(
                'app/urls.py',
                content='''from django.urls import path

    urlpatterns = []
    '''
            )

            # Overwrite existing file
            create_file('app/urls.py', content='...', overwrite=True)
    """
    file_path = Path(file_path)

    # Check if file exists
    if file_path.exists():
        if not overwrite:
            return False
        existing_content = file_path.read_text(encoding="utf-8")
        if existing_content == content:
            return False

    # Create parent directories if needed
    if create_dirs and not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    file_path.write_text(content, encoding="utf-8")
    return file_path.as_posix()
