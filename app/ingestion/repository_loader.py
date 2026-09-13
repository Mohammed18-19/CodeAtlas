import logging
from pathlib import Path
import subprocess
import tempfile
import zipfile


logger = logging.getLogger(__name__)


class RepositoryLoader:
    def load_from_github(self, repo_url: str) -> Path:
        destination = Path(tempfile.mkdtemp(prefix="codeatlas_"))

        logger.info("Cloning repository: %s", repo_url)

        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                repo_url,
                str(destination),
            ],
            check=True,
        )

        logger.info("Repository cloned successfully: %s", destination)

        return destination

    def load_from_zip(self, zip_path: str | Path) -> Path:
        destination = Path(tempfile.mkdtemp(prefix="codeatlas_"))

        logger.info("Extracting ZIP repository: %s", zip_path)

        with zipfile.ZipFile(zip_path, "r") as zip_file:
            zip_file.extractall(destination)

        logger.info("ZIP repository extracted successfully: %s", destination)

        return destination