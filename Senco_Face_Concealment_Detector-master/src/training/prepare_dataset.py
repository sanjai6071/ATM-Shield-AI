import os
import argparse
import urllib.request
import zipfile
from src.utils.logger import setup_logger

logger = setup_logger("DatasetPreparer")

def prepare_directories(base_dir: str = "data"):
    """Creates YOLO standard dataset directory structure."""
    subdirs = [
        os.path.join(base_dir, "images", "train"),
        os.path.join(base_dir, "images", "val"),
        os.path.join(base_dir, "labels", "train"),
        os.path.join(base_dir, "labels", "val"),
        os.path.join(base_dir, "raw")
    ]
    for d in subdirs:
        os.makedirs(d, exist_ok=True)
    logger.info(f"Directory structure ready under: {base_dir}")

def download_roboflow_dataset(api_key: str, workspace: str, project: str, version: int, base_dir: str = "data"):
    """Downloads face concealment dataset using Roboflow Python API."""
    try:
        from roboflow import Roboflow
    except ImportError:
        logger.error("Roboflow package not installed. Run 'pip install roboflow' to use this utility.")
        return

    logger.info(f"Connecting to Roboflow project {workspace}/{project}:v{version}...")
    rf = Roboflow(api_key=api_key)
    rf_project = rf.workspace(workspace).project(project)
    dataset = rf_project.version(version).download("yolov8", location=base_dir)
    logger.info(f"Dataset successfully downloaded to: {dataset.location}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare Face Concealment Dataset")
    parser.add_argument("--base_dir", type=str, default="data", help="Root directory for dataset")
    parser.add_argument("--rf_key", type=str, default=None, help="Optional Roboflow API key")
    parser.add_argument("--rf_workspace", type=str, default=None, help="Roboflow workspace")
    parser.add_argument("--rf_project", type=str, default=None, help="Roboflow project name")
    parser.add_argument("--rf_version", type=int, default=1, help="Roboflow version number")
    args = parser.parse_args()

    prepare_directories(args.base_dir)

    if args.rf_key and args.rf_workspace and args.rf_project:
        download_roboflow_dataset(
            api_key=args.rf_key,
            workspace=args.rf_workspace,
            project=args.rf_project,
            version=args.rf_version,
            base_dir=args.base_dir
        )
