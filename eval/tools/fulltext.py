import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from layer1 import Text
raw = Path(sys.argv[1]).read_text()
p = Text(); p.feed(raw)
import re
print(re.sub(r"\n\s*\n+", "\n", "".join(p.out)).strip())
