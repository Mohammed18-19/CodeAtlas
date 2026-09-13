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


def ingest_repository(repo_url: str) -> int:
    loader = RepositoryLoader()
    discovery = FileDiscovery()
    chunker = CodeChunker()
    chunk_storage = ChunkStorage()

    repository_path = None
    db = SessionLocal()

    try:
        repository_name = get_repository_name(repo_url)

        print("=" * 70)
        print("CodeAtlas Ingestion")
        print("=" * 70)
        print(f"Repository: {repository_name}")
        print(f"URL:        {repo_url}")
        print()

        # ---------------------------------------------------------
        # Check duplicate repository
        # ---------------------------------------------------------

        existing_repository = (
            db.query(Repository)
            .filter(Repository.name == repository_name)
            .first()
        )

        if existing_repository is not None:
            return existing_repository

        # ---------------------------------------------------------
        # Clone repository
        # ---------------------------------------------------------

        print("[1/5] Cloning repository...")

        repository_path = loader.load_from_github(repo_url)

        print(f"      Clone path: {repository_path}")
        print()

        # ---------------------------------------------------------
        # Discover files
        # ---------------------------------------------------------

        print("[2/5] Discovering files...")

        discovered_files = discovery.discover(repository_path)

        python_files = [
            path
            for path in discovered_files
            if path.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

        print(
            f"      Discovered files: {len(discovered_files)}"
        )

        print(
            f"      Python files:     {len(python_files)}"
        )

        print()

        # ---------------------------------------------------------
        # Create repository
        # ---------------------------------------------------------

        print("[3/5] Creating repository record...")

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

        print(f"      Repository ID: {repository_id}")
        print()

        # ---------------------------------------------------------
        # Process files
        # ---------------------------------------------------------

        print("[4/5] Processing Python files...")
        print()

        processed_files = 0
        skipped_files = 0
        total_chunks = 0

        for index, file_path in enumerate(
            python_files,
            start=1,
        ):
            relative_path = file_path.relative_to(repository_path)

            print(
                f"[{index}/{len(python_files)}] {relative_path}"
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
                    print("      No chunks found.")
                    processed_files += 1
                    continue

                chunk_storage.save_chunks(
                    file_id=file_record.id,
                    chunks=chunks,
                )

                processed_files += 1
                total_chunks += len(chunks)

                print(
                    f"      Chunks: {len(chunks)}"
                )

            except (SyntaxError, UnicodeDecodeError) as exc:
                db.rollback()

                skipped_files += 1

                print(
                    f"      SKIPPED: {type(exc).__name__}: {exc}"
                )

                continue

        # ---------------------------------------------------------
        # Update repository metadata
        # ---------------------------------------------------------

        repository.file_count = processed_files

        db.commit()

        # ---------------------------------------------------------
        # Summary
        # ---------------------------------------------------------

        print()
        print("[5/5] Ingestion complete.")
        print()

        print("=" * 70)
        print("Ingestion Summary")
        print("=" * 70)

        print(
            f"Repository ID:       {repository_id}"
        )

        print(
            f"Repository:          {repository_name}"
        )

        print(
            f"Discovered files:    {len(discovered_files)}"
        )

        print(
            f"Python files:        {len(python_files)}"
        )

        print(
            f"Processed files:     {processed_files}"
        )

        print(
            f"Skipped files:       {skipped_files}"
        )

        print(
            f"Total chunks:        {total_chunks}"
        )

        print("=" * 70)

        return repository_id

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
