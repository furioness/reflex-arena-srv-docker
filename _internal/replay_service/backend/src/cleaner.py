import logging
import shutil
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.parser import parse_finished_at_with_fallback

logger = logging.getLogger(__name__)

KiB = 1024
MiB = 1024 * KiB
GiB = 1024 * MiB


@dataclass(frozen=True)
class CleanerConfig:
    replay_folder: Path
    min_free_space_ratio: float
    min_replay_retention_bytes: int
    min_expected_disk_size_bytes: int
    clean_interval_seconds: int

    def __post_init__(self):
        assert 0 < self.min_free_space_ratio < 1
        assert self.clean_interval_seconds > 0


class Cleaner:
    def __init__(self, config: CleanerConfig):
        self.config = config

    def _get_disk_usage_safe(self) -> shutil._ntuple_diskusage | None:
        usage = shutil.disk_usage(self.config.replay_folder)

        # Sanity checks. ZFS or other things may break this
        if usage.total <= 0:
            logger.warning("Disk usage reports total<=0")
            return None

        if usage.free < 0 or usage.free > usage.total:
            logger.warning("Disk usage reports invalid free space")
            return None

        if usage.total < self.config.min_expected_disk_size_bytes:
            logger.warning(
                "Disk total size (%d) below expected minimum",
                usage.total,
            )
            return None

        return usage

    def _calculate_space_size_to_clean_up(self) -> int:
        usage = self._get_disk_usage_safe()
        if usage is None:
            logger.warning("Unable to determine disk usage!")
            return 0

        logger.info(
            "Disk free: %.1f%% (%d MiB)",
            usage.free / usage.total * 100,
            usage.free // MiB,
        )

        current_ratio = usage.free / usage.total
        overusage_ratio = self.config.min_free_space_ratio - current_ratio
        need_to_clean_bytes = int(overusage_ratio * usage.total)
        return need_to_clean_bytes if overusage_ratio > 0 else 0

    def clean_up_once(self):
        bytes_to_clean = self._calculate_space_size_to_clean_up()
        if bytes_to_clean == 0:
            logger.info("Disk usage is acceptable, skipping cleanup.")
            return

        replays = sorted(
            (
                (path, path.stat().st_size)
                for path in self.config.replay_folder.glob("*.rep.zip")
                if path.is_file()
            ),
            key=lambda replay: parse_finished_at_with_fallback(
                replay[0].name, datetime.max.replace(tzinfo=timezone.utc)
            ),
        )
        total_replay_bytes = sum(size for _, size in replays)

        freed_bytes = 0
        for replay_path, replay_size in replays:
            if (
                    total_replay_bytes - freed_bytes
                    < self.config.min_replay_retention_bytes
            ):
                logger.info("Reached minimum replay retention size, stopping cleanup")
                return

            replay_path.unlink(missing_ok=True)
            freed_bytes += replay_size
            logger.info(
                "Removed replay %s (%d MiB)", replay_path.name, replay_size // MiB
            )

            if freed_bytes >= bytes_to_clean:
                return

    def clean_up_forever(self):
        while True:
            try:
                self.clean_up_once()
            except Exception:
                logger.exception(
                    "Cleaner encountered an error, but will continue after sleep"
                )
            logger.info("Cleaner finished, sleeping...")
            time.sleep(self.config.clean_interval_seconds)
