"""Record portable unittest results; separate live MCP checks need a Desktop port."""
from pathlib import Path
import subprocess, sys
root=Path(__file__).resolve().parents[1]
result=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(root/'tests'),'-p','test_*.py','-v'],capture_output=True,text=True)
output=result.stdout+result.stderr
(root/'review/python-tests.txt').write_text(output,encoding='utf-8')
print(output)
raise SystemExit(result.returncode)
