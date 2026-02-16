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

    Args:
        file_path: Path to the file to modify
        anchor: String to search for in the file
        lines_to_insert: List of lines to insert (each line should include its own indentation)
        position: Insert 'before' or 'after' the anchor
        check_as_block: If True, check if all lines exist as a consecutive block in the file.
                       If False, check each line individually and insert only missing lines.
        skip_if_any_exists: If True, skip insertion if ANY line exists (all must be missing).
                           If False (default), insert only missing lines (filter out existing ones).

    Returns:
        The path of the modified file if lines were inserted, or False if no changes were made.

    Example:
        # Insert only missing imports (default behavior)
        insert_lines_in_file(
            'urls.py',
            anchor='from django.urls import',
            lines_to_insert=[
                'from django_toolkit.models import AutoModelRegistry',
                'from django_toolkit.views import AutoViewRegistry'
            ],
            position='after'
        )

        # Skip insertion if ANY line already exists
        insert_lines_in_file(
            'urls.py',
            anchor='from django.urls import',
            lines_to_insert=[
                'from django_toolkit.models import AutoModelRegistry',
                'from django_toolkit.views import AutoViewRegistry'
            ],
            position='after',
            skip_if_any_exists=True
        )

        # Insert multiple URL patterns as a block
        insert_lines_in_file(
            'urls.py',
            anchor='urlpatterns = [',
            lines_to_insert=[
                "    path('api/', include('api.urls')),",
                "    path('admin/', include('admin.urls')),"
            ],
            position='after',
            check_as_block=True
        )
    """
    file_path = Path(file_path)

    if not file_path.exists():
        return False

    # Read file content
    content = file_path.read_text(encoding="utf-8")

    # Check if lines already exist
    if check_as_block:
        # Check if all lines exist as a consecutive block
        block_to_check = "\n".join(lines_to_insert)
        if block_to_check in content:
            return False
    else:
        # Check each line individually
        if skip_if_any_exists:
            # Skip if ANY line exists (all must be missing)
            for line_to_check in lines_to_insert:
                if line_to_check in content:
                    return False
        else:
            # Skip only if ALL lines exist (filter out existing lines)
            lines_to_insert = [line for line in lines_to_insert if line not in content]
            if not lines_to_insert:
                return False  # All lines already exist

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

        # Insert all lines at the position
        for idx, line_to_insert in enumerate(lines_to_insert):
            lines.insert(insert_index + idx, line_to_insert)

        # Write back
        file_path.write_text("\n".join(lines), encoding="utf-8")
        return file_path.as_posix()

    for i, line in enumerate(lines):
        if anchor in line:
            # Insert before or after
            insert_index = i if position == "before" else i + 1

            # Insert all lines at the position
            for idx, line_to_insert in enumerate(lines_to_insert):
                lines.insert(insert_index + idx, line_to_insert)

            # Write back
            file_path.write_text("\n".join(lines), encoding="utf-8")
            return file_path.as_posix()

    return False


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
    if file_path.exists() and not overwrite:
        return False

    # Create parent directories if needed
    if create_dirs and not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    file_path.write_text(content, encoding="utf-8")
    return file_path.as_posix()
