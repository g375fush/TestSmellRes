import os
import subprocess
import sys
from pathlib import Path

import tqdm

DETECTOR_OUTPUT = Path(sys.argv[1])
PLUGIN_ROOT = Path(sys.argv[0]).parent
REPO_PREFIX = Path(sys.argv[2])
PYTHON_INTERPRETER_NAME = 'Python 3.10'

PROJECT_LIST = [p for p in REPO_PREFIX.iterdir() if p.is_dir()]

with (DETECTOR_OUTPUT / 'log.txt').open('w') as f:
    pass

for project in tqdm.tqdm(PROJECT_LIST):
    process = subprocess.run(
        [PLUGIN_ROOT / ('gradlew.bat' if os.name == 'nt' else 'gradlew'), '-p', str(PLUGIN_ROOT), 'runIde',
         f'-PmyPath="{project}"' if os.name == 'nt' else f'-PmyPath={project}',
         f'-PmyPython="{PYTHON_INTERPRETER_NAME}"' if os.name == 'nt' else f'-PmyPython={PYTHON_INTERPRETER_NAME}',
         f'-PmyOutDir="{DETECTOR_OUTPUT}"' if os.name == 'nt' else f'-PmyOutDir={DETECTOR_OUTPUT}'],
        capture_output=True,
        text=True
    )

    with (DETECTOR_OUTPUT / 'log.txt').open('a') as f:
        f.write(f'{project=}\n====STDOUT====\n{process.stdout}\n====STDERR===={process.stderr}\n\n')
