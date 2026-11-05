"""Regenerate the 2025 export-backed model. Kept for compatibility with older build commands."""
from pathlib import Path
import runpy
if __name__=='__main__':runpy.run_path(str(Path(__file__).with_name('import_export.py')),run_name='__main__')
