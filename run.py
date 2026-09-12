import os
import sys
import argparse

# Fix OpenMP DLL conflict on Windows
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from src.main import run_pipeline, parse_args
from src.video_generator import generate_synthetic_surveillance_video

if __name__ == "__main__":
    args = parse_args()
    if args.generate_synthetic or not os.path.exists(args.input):
        generate_synthetic_surveillance_video(args.input)
    run_pipeline(args.input, args.output_dir)
