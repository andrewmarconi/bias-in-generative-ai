"""
File Management Utilities for TUI.

Provides log rotation, cleanup, backup, and file organization.
"""

import logging
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
import gzip

logger = logging.getLogger(__name__)


class FileManager:
    """
    Comprehensive file management for the TUI system.

    Handles:
    - Log file rotation and cleanup
    - Session file organization and cleanup
    - Configuration backup and versioning
    - Disk space monitoring
    """

    def __init__(self, base_dir: Path):
        """
        Initialize file manager.

        Args:
            base_dir: Base directory for all file operations
        """
        self.base_dir = Path(base_dir)
        self.logs_dir = self.base_dir / "logs"
        self.sessions_dir = self.base_dir / "sessions"
        self.backups_dir = self.base_dir / "backups"
        self.archive_dir = self.base_dir / "archive"

        # Create directories
        for dir_path in [self.logs_dir, self.backups_dir, self.archive_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def rotate_log_files(self, max_size_mb: int = 10, max_files: int = 5) -> None:
        """
        Rotate log files when they exceed size limits.

        Args:
            max_size_mb: Maximum size in MB before rotation
            max_files: Maximum number of rotated files to keep
        """
        log_files = list(self.logs_dir.glob("*.log"))

        for log_file in log_files:
            if log_file.stat().st_size > max_size_mb * 1024 * 1024:
                self._rotate_file(log_file, max_files)

    def _rotate_file(self, file_path: Path, max_files: int) -> None:
        """
        Rotate a single file.

        Args:
            file_path: File to rotate
            max_files: Maximum rotated files to keep
        """
        base_name = file_path.stem
        extension = file_path.suffix

        # Compress current file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rotated_name = f"{base_name}_{timestamp}{extension}.gz"
        rotated_path = self.logs_dir / rotated_name

        try:
            with open(file_path, 'rb') as f_in:
                with gzip.open(rotated_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Clear original file
            file_path.write_text("")

            logger.info(f"Rotated log file: {file_path} -> {rotated_path}")

            # Clean up old rotated files
            self._cleanup_old_files(self.logs_dir, f"{base_name}_*{extension}.gz", max_files)

        except Exception as e:
            logger.error(f"Failed to rotate file {file_path}: {e}")

    def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """
        Clean up old completed/cancelled sessions.

        Args:
            max_age_days: Maximum age in days for cleanup

        Returns:
            Number of sessions cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        cleaned_count = 0

        session_files = list(self.sessions_dir.glob("exp_*.json"))

        for session_file in session_files:
            try:
                # Check file modification time
                if session_file.stat().st_mtime < cutoff_date.timestamp():
                    # Load session to check status
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)

                    status = session_data.get("status", "unknown")

                    # Only clean up completed, cancelled, or failed sessions
                    if status in ["completed", "cancelled", "failed"]:
                        # Move to archive before deleting
                        archive_name = f"archived_{session_file.name}"
                        archive_path = self.archive_dir / archive_name
                        shutil.move(session_file, archive_path)

                        cleaned_count += 1
                        logger.info(f"Archived old session: {session_file} -> {archive_path}")

            except Exception as e:
                logger.error(f"Error processing session file {session_file}: {e}")

        return cleaned_count

    def backup_configuration(self, config_path: Path, backup_name: Optional[str] = None) -> Path:
        """
        Create a backup of a configuration file.

        Args:
            config_path: Path to configuration file
            backup_name: Optional name for backup (auto-generated if None)

        Returns:
            Path to created backup file
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{config_path.stem}_{timestamp}{config_path.suffix}"

        backup_path = self.backups_dir / backup_name

        shutil.copy2(config_path, backup_path)
        logger.info(f"Configuration backup created: {config_path} -> {backup_path}")

        return backup_path

    def list_configuration_backups(self) -> List[Dict[str, Any]]:
        """
        List available configuration backups.

        Returns:
            List of backup information dictionaries
        """
        backups = []

        for backup_file in self.backups_dir.glob("*"):
            if backup_file.is_file():
                stat = backup_file.stat()
                backups.append({
                    "name": backup_file.name,
                    "path": backup_file,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_mtime),
                    "modified": datetime.fromtimestamp(stat.st_mtime)
                })

        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x["created"], reverse=True)

        return backups

    def restore_configuration_backup(self, backup_name: str, target_path: Path) -> None:
        """
        Restore a configuration from backup.

        Args:
            backup_name: Name of backup file
            target_path: Path to restore to

        Raises:
            FileNotFoundError: If backup doesn't exist
        """
        backup_path = self.backups_dir / backup_name

        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_name}")

        shutil.copy2(backup_path, target_path)
        logger.info(f"Configuration restored from backup: {backup_path} -> {target_path}")

    def get_disk_usage(self) -> Dict[str, int]:
        """
        Get disk usage statistics for managed directories.

        Returns:
            Dictionary with directory sizes in bytes
        """
        usage = {}

        for dir_path in [self.logs_dir, self.sessions_dir, self.backups_dir, self.archive_dir]:
            total_size = 0
            try:
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
            except Exception:
                pass  # Skip directories we can't access

            usage[dir_path.name] = total_size

        return usage

    def cleanup_temp_files(self) -> int:
        """
        Clean up temporary files and cache.

        Returns:
            Number of files cleaned up
        """
        cleaned_count = 0

        # Clean up .tmp files
        for tmp_file in self.base_dir.rglob("*.tmp"):
            try:
                tmp_file.unlink()
                cleaned_count += 1
            except Exception:
                pass

        # Clean up __pycache__ directories
        for pycache_dir in self.base_dir.rglob("__pycache__"):
            try:
                shutil.rmtree(pycache_dir)
                cleaned_count += 1
            except Exception:
                pass

        logger.info(f"Cleaned up {cleaned_count} temporary files")
        return cleaned_count

    def _cleanup_old_files(self, directory: Path, pattern: str, max_files: int) -> None:
        """
        Clean up old files matching a pattern, keeping only the most recent.

        Args:
            directory: Directory to clean
            pattern: Glob pattern for files to clean
            max_files: Maximum number of files to keep
        """
        files = list(directory.glob(pattern))

        if len(files) > max_files:
            # Sort by modification time (oldest first)
            files.sort(key=lambda x: x.stat().st_mtime)

            # Remove oldest files
            for old_file in files[:-max_files]:
                try:
                    old_file.unlink()
                    logger.debug(f"Cleaned up old file: {old_file}")
                except Exception as e:
                    logger.error(f"Failed to clean up {old_file}: {e}")

    def archive_old_data(self, archive_name: str, source_dirs: List[str]) -> Path:
        """
        Create an archive of old data for long-term storage.

        Args:
            archive_name: Name for the archive file
            source_dirs: List of directory names to archive

        Returns:
            Path to created archive
        """
        archive_path = self.archive_dir / f"{archive_name}.tar.gz"

        # Create archive
        import tarfile

        with tarfile.open(archive_path, "w:gz") as tar:
            for dir_name in source_dirs:
                source_path = self.base_dir / dir_name
                if source_path.exists():
                    tar.add(source_path, arcname=dir_name)

        logger.info(f"Created data archive: {archive_path}")
        return archive_path