import os
import sys
from pathlib import Path
import datalad.api as dl
from datalad.api import Dataset
from datetime import datetime
from contextlib import contextmanager
import logging
import shutil
import argparse

# Create logs directory
os.makedirs("logs", exist_ok=True)

# Configure base logging
base_log_filename = f"logs/hcp_download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(base_log_filename),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@contextmanager
def log_operation(subject, data_type, operation="get", log_dir="logs"):
    """
    Context manager to create separate log file for each operation

    Args:
        subject: Subject ID (e.g., "116726")
        data_type: Type of data being downloaded (e.g., "T1w_MPR1", "tfMRI_MOTOR_LR")
        operation: Type of operation (e.g., "get", "organize")
        log_dir: Directory to save logs
    """
    data_type = data_type.replace('/', '_')

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f"{log_dir}/{operation}_{subject}_{data_type}_{timestamp}.log"

    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

    logger.info(f"Starting {operation}: Subject {subject}, Data type {data_type}")
    logger.info(f"Operation log file: {log_filename}")

    try:
        yield log_filename
    except Exception as e:
        logger.error(f"Error during {operation}: {e}")
        raise
    finally:
        logger.info(f"Completed {operation} for Subject {subject}, Data type {data_type}")
        root_logger.removeHandler(file_handler)
        file_handler.close()


def setup_dataset(repo_url, local_path):
    """
    Clone or update the HCP dataset
    """
    logger.info(f"Setting up dataset at {local_path}")

    if os.path.exists(local_path):
        logger.info("Dataset already exists, using existing dataset...")
        ds = Dataset(local_path)
    else:
        logger.info("Cloning dataset...")
        try:
            ds = dl.clone(repo_url, local_path)
        except Exception as e:
            if "dubious ownership" in str(e):
                logger.error("Git ownership issue during clone!")
                logger.error("To fix this, run:")
                logger.error(f"git config --global --add safe.directory {os.path.abspath(local_path)}")
                logger.error("Then re-run this script.")
                raise
            else:
                raise

    return ds


def download_specific_files(ds, subject, data_specs):
    """
    Download only the specific files needed for each data type

    Args:
        ds: DataLad Dataset object
        subject: Subject ID
        data_specs: Dictionary mapping data types to file patterns to download
    """
    for data_type, file_patterns in data_specs.items():
        logger.info(f"Downloading {data_type} for subject {subject}")

        with log_operation(subject, data_type, "get") as log_file:
            # Download the entire directory for this data type
            # DataLad doesn't handle wildcards well, so we download the whole directory
            dir_path = f"HCP1200/{subject}/unprocessed/3T/{data_type}"
            try:
                logger.info(f"Getting: {dir_path}")
                result = ds.get(dir_path)
                logger.info(f"Successfully downloaded {dir_path}")
            except Exception as e:
                logger.error(f"Failed to download {dir_path}: {e}")


def unlock_file(ds, file_path):
    """
    Unlock a single file if it's a symlink (annexed file)

    Args:
        ds: DataLad Dataset object
        file_path: Path object to the file

    Returns:
        Path object to use for copying (unlocked file or resolved symlink)
    """
    if file_path.is_symlink():
        logger.info(f"File is annexed (symlink), unlocking: {file_path}")
        try:
            ds.unlock(str(file_path))
            logger.info(f"Successfully unlocked {file_path}")
            return file_path
        except Exception as e:
            logger.warning(f"Could not unlock {file_path}, will use resolved path: {e}")
            return file_path.resolve()
    return file_path


def copy_evs_directory(ds, source_evs_dir, dest_evs_dir):
    """
    Copy all files from the EVs directory, unlocking them if needed

    Args:
        ds: DataLad Dataset object
        source_evs_dir: Source EVs directory Path
        dest_evs_dir: Destination EVs directory Path
    """
    if not source_evs_dir.exists():
        logger.warning(f"EVs directory does not exist: {source_evs_dir}")
        return

    # Create destination directory
    dest_evs_dir.mkdir(parents=True, exist_ok=True)

    # Copy all files in the EVs directory
    for ev_file in source_evs_dir.iterdir():
        if ev_file.is_file():
            dest_file = dest_evs_dir / ev_file.name

            # Unlock if needed
            source_to_copy = unlock_file(ds, ev_file)

            # Copy the file
            logger.info(f"Copying EV file {ev_file.name}")
            try:
                shutil.copy2(source_to_copy, dest_file)
                logger.info(f"Successfully copied to {dest_file}")
            except Exception as e:
                logger.error(f"Failed to copy {ev_file} to {dest_file}: {e}")


def organize_files(ds, subject, source_base, dest_base, task_runs):
    """
    Organize downloaded files into task-specific and STRUCTURAL directories
    Unlocks files so they are actual copies, not symlinks

    Args:
        ds: DataLad Dataset object
        subject: Subject ID
        source_base: Base path where files were downloaded
        dest_base: Base path for organized output
        task_runs: List of tuples (task_name, run_direction) e.g., [("MOTOR", "LR"), ("GAMBLING", "LR")]
    """
    logger.info(f"Organizing files for subject {subject}")

    with log_operation(subject, "organization", "organize") as log_file:
        # Process task-specific files
        for task, run_dir in task_runs:
            task_dir_name = f"tfMRI_{task}_{run_dir}"

            # Copy the main nifti file
            nifti_filename = f"{subject}_3T_{task_dir_name}.nii.gz"
            source_nifti = Path(source_base) / "HCP1200" / subject / "unprocessed" / "3T" / task_dir_name / nifti_filename
            dest_nifti = Path(dest_base) / task / subject / "unprocessed" / "3T" / task_dir_name / nifti_filename

            if source_nifti.exists():
                dest_nifti.parent.mkdir(parents=True, exist_ok=True)
                source_to_copy = unlock_file(ds, source_nifti)

                logger.info(f"Copying {source_nifti} -> {dest_nifti}")
                try:
                    shutil.copy2(source_to_copy, dest_nifti)
                    logger.info(f"Successfully copied to {dest_nifti}")
                except Exception as e:
                    logger.error(f"Failed to copy {source_nifti} to {dest_nifti}: {e}")
            else:
                logger.warning(f"Source file does not exist: {source_nifti}")

            # Copy all EV files
            source_evs_dir = Path(source_base) / "HCP1200" / subject / "unprocessed" / "3T" / task_dir_name / "LINKED_DATA" / "EPRIME" / "EVs"
            dest_evs_dir = Path(dest_base) / task / subject / "unprocessed" / "3T" / task_dir_name / "LINKED_DATA" / "EPRIME" / "EVs"

            copy_evs_directory(ds, source_evs_dir, dest_evs_dir)

        # Process STRUCTURAL file
        structural_filename = f"{subject}_3T_T1w_MPR1.nii.gz"
        source_structural = Path(source_base) / "HCP1200" / subject / "unprocessed" / "3T" / "T1w_MPR1" / structural_filename
        dest_structural = Path(dest_base) / "STRUCTURAL" / subject / "unprocessed" / "3T" / "T1w_MPR1" / structural_filename

        if source_structural.exists():
            dest_structural.parent.mkdir(parents=True, exist_ok=True)
            source_to_copy = unlock_file(ds, source_structural)

            logger.info(f"Copying {source_structural} -> {dest_structural}")
            try:
                shutil.copy2(source_to_copy, dest_structural)
                logger.info(f"Successfully copied to {dest_structural}")
            except Exception as e:
                logger.error(f"Failed to copy {source_structural} to {dest_structural}: {e}")
        else:
            logger.warning(f"Source file does not exist: {source_structural}")


def remove_unwanted_directories(ds, subject, keep_patterns):
    """
    Remove unwanted directories from downloaded data using file system operations

    Args:
        ds: DataLad Dataset object
        subject: Subject ID
        keep_patterns: List of directory names to keep (e.g., ["T1w_MPR1", "tfMRI_MOTOR_LR"])
    """
    logger.info(f"Removing unwanted data for subject {subject}")

    rm_paths = ["3T", "7T", "MEG"]

    for rm_path in rm_paths:
        subject_rm_path = Path(ds.path) / "HCP1200" / subject / "unprocessed" / rm_path

        if subject_rm_path.exists():
            all_dirs = [d for d in subject_rm_path.iterdir() if d.is_dir()]

            for dir_path in all_dirs:
                dir_name = dir_path.name

                if dir_name not in keep_patterns:
                    logger.info(f"Removing directory: {dir_path}")
                    try:
                        shutil.rmtree(dir_path)
                        logger.info(f"Successfully removed {dir_name} for {subject}")
                    except Exception as e:
                        logger.error(f"Failed to remove {dir_name} for {subject}: {e}")
                else:
                    logger.info(f"Keeping directory: {dir_name} for {subject}")
        else:
            logger.warning(f"Subject rm directory not found: {subject_rm_path}")


def cleanup_dataset_files(ds, subject, task_runs):
    """
    Clean up downloaded files from the dataset path after organizing

    Args:
        ds: DataLad Dataset object
        subject: Subject ID
        task_runs: List of tuples (task_name, run_direction)
    """
    logger.info(f"Cleaning up dataset files for subject {subject}")

    # Clean up task-specific directories
    for task, run_dir in task_runs:
        task_dir_name = f"tfMRI_{task}_{run_dir}"
        task_path = Path(ds.path) / "HCP1200" / subject / "unprocessed" / "3T" / task_dir_name

        if task_path.exists():
            logger.info(f"Removing {task_path}")
            try:
                shutil.rmtree(task_path)
                logger.info(f"Successfully removed {task_path}")
            except Exception as e:
                logger.error(f"Failed to remove {task_path}: {e}")

    # Clean up structural directory
    structural_path = Path(ds.path) / "HCP1200" / subject / "unprocessed" / "3T" / "T1w_MPR1"
    if structural_path.exists():
        logger.info(f"Removing {structural_path}")
        try:
            shutil.rmtree(structural_path)
            logger.info(f"Successfully removed {structural_path}")
        except Exception as e:
            logger.error(f"Failed to remove {structural_path}: {e}")

    # Check if the subject's 3T directory is empty and remove it
    subject_3t_path = Path(ds.path) / "HCP1200" / subject / "unprocessed" / "3T"
    if subject_3t_path.exists() and not any(subject_3t_path.iterdir()):
        logger.info(f"Removing empty directory {subject_3t_path}")
        try:
            subject_3t_path.rmdir()
            logger.info(f"Successfully removed {subject_3t_path}")
        except Exception as e:
            logger.error(f"Failed to remove {subject_3t_path}: {e}")


def parse_task_runs(task_runs_str):
    """
    Parse task runs from command line argument

    Args:
        task_runs_str: Comma-separated string like "MOTOR:LR,MOTOR:RL,GAMBLING:LR"

    Returns:
        List of tuples: [("MOTOR", "LR"), ("MOTOR", "RL"), ("GAMBLING", "LR")]
    """
    task_runs = []
    for task_run in task_runs_str.split(','):
        task_run = task_run.strip()
        if ':' in task_run:
            task, run_dir = task_run.split(':')
            task_runs.append((task.strip(), run_dir.strip()))
        else:
            logger.warning(f"Skipping invalid task run format: {task_run} (expected format: TASK:DIRECTION)")
    return task_runs


def main():
    parser = argparse.ArgumentParser(
        description='Download and organize HCP data using DataLad',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download MOTOR LR for a single subject
  python download_data.py --subjects 116726 --tasks MOTOR:LR

  # Download multiple tasks for multiple subjects
  python download_data.py --subjects 116726,118528 --tasks MOTOR:LR,MOTOR:RL,GAMBLING:LR

  # Specify custom paths
  python download_data.py --subjects 116726 --tasks MOTOR:LR \\
    --dataset-path /custom/hcp/path \\
    --output-path /custom/output/path
        """
    )

    parser.add_argument(
        '--subjects',
        type=str,
        required=True,
        help='Comma-separated list of subject IDs (e.g., "116726,118528,131823")'
    )

    parser.add_argument(
        '--tasks',
        type=str,
        required=True,
        help='Comma-separated list of task:direction pairs (e.g., "MOTOR:LR,MOTOR:RL,GAMBLING:LR")'
    )

    parser.add_argument(
        '--dataset-path',
        type=str,
        default="/Users/zenkavi/Documents/EnkaviLab/data/hcp/",
        help='Path where HCP dataset will be cloned/exists (default: /Users/zenkavi/Documents/EnkaviLab/data/hcp/)'
    )

    parser.add_argument(
        '--output-path',
        type=str,
        default="/Users/zenkavi/Documents/EnkaviLab/hcp_multi_pipelines/data/original",
        help='Path where organized files will be saved (default: /Users/zenkavi/Documents/EnkaviLab/hcp_multi_pipelines/data/original)'
    )

    args = parser.parse_args()

    # Configuration
    REPO_URL = "https://github.com/datalad-datasets/human-connectome-project-openaccess"
    LOCAL_DATASET_PATH = args.dataset_path
    OUTPUT_BASE_PATH = args.output_path

    # Parse subject list
    subject_list = [s.strip() for s in args.subjects.split(',')]

    # Parse task runs
    task_runs = parse_task_runs(args.tasks)

    if not task_runs:
        logger.error("No valid task runs specified. Use format: TASK:DIRECTION (e.g., MOTOR:LR)")
        sys.exit(1)

    logger.info(f"Processing {len(subject_list)} subjects: {', '.join(subject_list)}")
    logger.info(f"Task runs: {', '.join([f'{t}:{d}' for t, d in task_runs])}")
    logger.info(f"Dataset path: {LOCAL_DATASET_PATH}")
    logger.info(f"Output path: {OUTPUT_BASE_PATH}")

    # Data specifications: only download what we need
    # This is constructed from task_runs
    data_specs = {}
    for task, run_dir in task_runs:
        task_dir_name = f"tfMRI_{task}_{run_dir}"
        data_specs[task_dir_name] = [
            f"{task_dir_name}/*_3T_{task_dir_name}.nii.gz",
            f"{task_dir_name}/LINKED_DATA/EPRIME/EVs/*.txt"
        ]

    # Always download structural data
    # data_specs["T1w_MPR1"] = [
    #     "T1w_MPR1/*_3T_T1w_MPR1.nii.gz"
    # ]

    # Setup dataset once
    logger.info("Setting up HCP dataset")
    ds = setup_dataset(REPO_URL, LOCAL_DATASET_PATH)

    # Build keep_patterns from data_specs (directories we actually want to keep)
    keep_patterns = list(data_specs.keys())

    # Process each subject
    for subject in subject_list:
        logger.info(f"Processing subject {subject}")

        # Download specific files
        download_specific_files(ds, subject, data_specs)

        # Remove unwanted directories that were downloaded (because sub-datasets download everything)
        remove_unwanted_directories(ds, subject, keep_patterns)

        # Organize files into task-specific and STRUCTURAL directories
        organize_files(ds, subject, LOCAL_DATASET_PATH, OUTPUT_BASE_PATH, task_runs)

        # Clean up downloaded files from dataset path to save space
        cleanup_dataset_files(ds, subject, task_runs)

    logger.info("All downloads and organization completed")


if __name__ == "__main__":
    main()
