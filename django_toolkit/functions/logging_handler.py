import re
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler


class DTProjectDailyFileHandler(TimedRotatingFileHandler):
    """Daily rotating file handler with rotated filenames: YYYY-MM-DD.<projectname>.log"""

    def __init__(self, filename, when='midnight', interval=1, backupCount=100, encoding='utf-8', delay=False, utc=False, atTime=None):
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(
            filename=str(path),
            when=when,
            interval=interval,
            backupCount=backupCount,
            encoding=encoding,
            delay=delay,
            utc=utc,
            atTime=atTime,
        )
        self._project_name = path.stem

    def rotation_filename(self, default_name):
        default_path = Path(default_name)
        match = re.search(r"(\d{4}-\d{2}-\d{2})$", default_path.name)
        if not match:
            return default_name
        date_part = match.group(1)
        return str(default_path.with_name(f"{date_part}.{self._project_name}.log"))

    def getFilesToDelete(self):
        if self.backupCount <= 0:
            return []

        log_dir = Path(self.baseFilename).parent
        pattern = re.compile(rf"^\d{{4}}-\d{{2}}-\d{{2}}\.{re.escape(self._project_name)}\.log$")
        candidates = sorted(
            str(path)
            for path in log_dir.iterdir()
            if path.is_file() and pattern.match(path.name)
        )
        if len(candidates) <= self.backupCount:
            return []
        return candidates[: len(candidates) - self.backupCount]
