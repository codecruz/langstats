"""Entry point used by the launchers.

It only imports langstats.py as a module, so Python caches its bytecode in
__pycache__ instead of recompiling the whole script on every hook call.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import langstats  # noqa: E402

sys.exit(langstats.main())
