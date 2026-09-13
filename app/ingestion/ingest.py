import argparse
import shutil
from pathlib import Path
from urllib.parse import urlparse

from app.database import SessionLocal
from app.ingestion.repository_loader import RepositoryLoader
from app.ingestion.file_discovery import FileDiscovery
from app.ingestion.chunking.code_chunker import CodeChunker
from app.ingestion.chunk_storage import ChunkStorage
from app.models import Repository, File


SUPPORTED_EXTENSIONS = {
    ".py",
}


def get_repository_name(repo_url: str) -> str:
    parsed = urlparse(repo_url)

    path = parsed.path.rstrip("/")
    name = Path(path).name

    if name.endswith(".git"):
        name = name[:-4]

    if not name:
        raise ValueError(
            f"Could not determine repository name from URL: {repo_url}"
        )

    return name


def ingest_repository(
    repo_url: str,
    progress_callback=None,
):
    def progress(**updates):
        if progress_callback:
            progress_callback(**updates)

    loader = RepositoryLoader()
    discovery = FileDiscovery()
    chunker = CodeChunker()
    chunk_storage = ChunkStorage()

    repository_path = None
    db = SessionLocal()

    try:
        repository_name = get_repository_name(repo_url)

        # ---------------------------------------------------------
        # Check duplicate repository
        # ---------------------------------------------------------

        progress(
            phase="checking",
            progress=15,
            message="Checking existing repositories...",
        )

        existing_repository = (
            db.query(Repository)
            .filter(Repository.name == repository_name)
            .first()
        )

        if existing_repository is not None:
            progress(
                phase="ready",
                progress=100,
                message="Repository already exists.",
            )

            return {
                "id": existing_repository.id,
                "name": existing_repository.name,
                "file_count": existing_repository.file_count,
            }

        # ---------------------------------------------------------
        # Clone
        # ---------------------------------------------------------

        progress(
            phase="cloning",
            progress=20,
            message="Cloning repository...",
        )

        repository_path = loader.load_from_github(repo_url)

        # ---------------------------------------------------------
        # Discover
        # ---------------------------------------------------------

        progress(
            phase="discovering",
            progress=35,
            message="Discovering source files...",
        )

        discovered_files = discovery.discover(repository_path)

        python_files = [
            path
            for path in discovered_files
            if path.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

        # ---------------------------------------------------------
        # Create repository
        # ---------------------------------------------------------

        progress(
            phase="creating",
            progress=45,
            message="Creating repository record...",
        )

        repository = Repository(
            name=repository_name,
            repo_metadata={
                "source": "github",
                "url": repo_url,
            },
            file_count=0,
        )

        db.add(repository)
        db.commit()
        db.refresh(repository)

        repository_id = repository.id

        # ---------------------------------------------------------
        # Process files
        # ---------------------------------------------------------

        total_files = len(python_files)
        processed_files = 0
        skipped_files = 0
        total_chunks = 0

        for index, file_path in enumerate(
            python_files,
            start=1,
        ):
            relative_path = file_path.relative_to(repository_path)

            if total_files:
                file_progress = 50 + int(
                    (index / total_files) * 45
                )
            else:
                file_progress = 95

            progress(
                phase="processing",
                progress=file_progress,
                message=(
                    f"Processing {index}/{total_files}: "
                    f"{relative_path}"
                ),
            )

            try:
                metadata = discovery.get_metadata(file_path)

                file_record = File(
                    repository_id=repository_id,
                    path=str(relative_path),
                    filename=metadata["filename"],
                    language=metadata["language"],
                    file_size=metadata["file_size"],
                )

                db.add(file_record)
                db.commit()
                db.refresh(file_record)

                chunks = chunker.chunk_file(
                    file_path=file_path,
                    display_path=str(relative_path),
                )

                if not chunks:
                    processed_files += 1
                    continue

                chunk_storage.save_chunks(
                    file_id=file_record.id,
                    chunks=chunks,
                )

                processed_files += 1
                total_chunks += len(chunks)

            except (SyntaxError, UnicodeDecodeError):
                db.rollback()
                skipped_files += 1

        repository.file_count = processed_files
        db.commit()

        progress(
            phase="finalizing",
            progress=98,
            message="Finalizing repository...",
        )

        return {
            "id": repository_id,
            "name": repository_name,
            "file_count": processed_files,
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

        if repository_path is not None:
            shutil.rmtree(
                repository_path,
                ignore_errors=True,
            )


def main():
    parser = argparse.ArgumentParser(
        description="Ingest a GitHub repository into CodeAtlas."
    )

    parser.add_argument(
        "repo_url",
        help="GitHub repository URL",
    )

    args = parser.parse_args()

    try:
        ingest_repository(args.repo_url)

    except Exception as exc:
        print()
        print("=" * 70)
        print("INGESTION FAILED")
        print("=" * 70)
        print(f"{type(exc).__name__}: {exc}")
        print("=" * 70)

        raise SystemExit(1)


if __name__ == "__main__":
    main()
