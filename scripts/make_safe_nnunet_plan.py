#!/usr/bin/env python3
"""Add a reduced-patch 3D configuration without altering the original plan."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("plans", type=Path)
    parser.add_argument("--configuration", default="3d_safe96")
    args = parser.parse_args()

    plans = json.loads(args.plans.read_text())
    source = plans["configurations"]["3d_fullres"]
    safe = copy.deepcopy(source)
    safe["patch_size"] = [96, 96, 96]
    # Preprocessed arrays are full volumes and remain valid; only sampling changes.
    safe["data_identifier"] = source["data_identifier"]
    plans["configurations"][args.configuration] = safe
    args.plans.write_text(json.dumps(plans, indent=2) + "\n")
    print(f"Added {args.configuration} with patch {safe['patch_size']} and batch {safe['batch_size']}")


if __name__ == "__main__":
    main()
