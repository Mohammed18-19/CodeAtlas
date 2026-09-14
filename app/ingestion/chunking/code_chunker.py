import ast
from pathlib import Path

from app.ingestion.rag.security import redact_secrets


class CodeChunker:
    def chunk_file(
        self,
        file_path: Path,
        display_path: str | None = None,
    ) -> list[dict]:

        content = file_path.read_text(
            encoding="utf-8"
        )

        if not content.strip():
            return []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []

        lines = content.splitlines()
        chunks = []

        source_path = (
            display_path
            if display_path is not None
            else file_path.as_posix()
        )

        def add_chunk(
            source: str,
            start_line: int,
            end_line: int,
            symbol: str,
            symbol_type: str,
        ) -> None:

            source = source.strip()
            source = redact_secrets(source)

            if not source:
                return

            enriched_content = (
                f"File: {source_path}\n"
                f"Symbol: {symbol}\n"
                f"Symbol Type: {symbol_type}\n\n"
                f"{source}"
            )

            chunks.append(
                {
                    "content": enriched_content,
                    "start_line": start_line,
                    "end_line": end_line,
                    "symbol": symbol,
                    "symbol_type": symbol_type,
                }
            )

        for node in tree.body:

            if not hasattr(node, "lineno"):
                continue

            # -----------------------------------------------------
            # Class
            # -----------------------------------------------------

            if isinstance(node, ast.ClassDef):

                class_start = node.lineno

                if node.body:
                    header_end = (
                        node.body[0].lineno - 1
                    )
                else:
                    header_end = node.end_lineno

                if header_end >= class_start:
                    add_chunk(
                        source="\n".join(
                            lines[
                                class_start - 1:
                                header_end
                            ]
                        ),
                        start_line=class_start,
                        end_line=header_end,
                        symbol=node.name,
                        symbol_type="class",
                    )

                # -------------------------------------------------
                # Methods
                # -------------------------------------------------

                for child in node.body:

                    if not hasattr(child, "lineno"):
                        continue

                    if isinstance(
                        child,
                        (
                            ast.FunctionDef,
                            ast.AsyncFunctionDef,
                        ),
                    ):

                        start_line = child.lineno
                        end_line = child.end_lineno

                        add_chunk(
                            source="\n".join(
                                lines[
                                    start_line - 1:
                                    end_line
                                ]
                            ),
                            start_line=start_line,
                            end_line=end_line,
                            symbol=(
                                f"{node.name}."
                                f"{child.name}"
                            ),
                            symbol_type="method",
                        )

            # -----------------------------------------------------
            # Module-level function
            # -----------------------------------------------------

            elif isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            ):

                start_line = node.lineno
                end_line = node.end_lineno

                add_chunk(
                    source="\n".join(
                        lines[
                            start_line - 1:
                            end_line
                        ]
                    ),
                    start_line=start_line,
                    end_line=end_line,
                    symbol=node.name,
                    symbol_type="function",
                )

            # -----------------------------------------------------
            # Other declarations
            # -----------------------------------------------------

            else:

                start_line = node.lineno
                end_line = node.end_lineno

                source = "\n".join(
                    lines[
                        start_line - 1:
                        end_line
                    ]
                )

                if isinstance(node, ast.Assign):

                    names = []

                    for target in node.targets:

                        if isinstance(
                            target,
                            ast.Name,
                        ):
                            names.append(
                                target.id
                            )

                    symbol = (
                        ", ".join(names)
                        if names
                        else type(node).__name__
                    )

                    symbol_type = "assignment"

                elif isinstance(
                    node,
                    ast.AnnAssign,
                ):

                    if isinstance(
                        node.target,
                        ast.Name,
                    ):
                        symbol = node.target.id
                    else:
                        symbol = type(node).__name__

                    symbol_type = "assignment"

                elif isinstance(
                    node,
                    ast.Import,
                ):

                    symbol = "imports"
                    symbol_type = "import"

                elif isinstance(
                    node,
                    ast.ImportFrom,
                ):

                    symbol = (
                        f"import {node.module}"
                    )
                    symbol_type = "import"

                else:

                    symbol = type(node).__name__
                    symbol_type = "other"

                add_chunk(
                    source=source,
                    start_line=start_line,
                    end_line=end_line,
                    symbol=symbol,
                    symbol_type=symbol_type,
                )

        return chunks
