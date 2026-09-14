import re

from app.ingestion.retrievalreranking.hybrid_search import HybridSearch
from app.ingestion.retrievalreranking.reranker import Reranker
from app.ingestion.retrievalreranking.file_search import FileSearch
from app.ingestion.retrievalreranking.query_router import QueryRouter
from app.ingestion.rag.context_builder import ContextBuilder
from app.ingestion.rag.generator import RAGGenerator
from app.ingestion.rag.conversation_manager import ConversationManager
from app.ingestion.rag.security import (
    contains_sensitive_request,
    safe_security_response,
)


class RAGPipeline:

    def __init__(self):
        self.hybrid_search = HybridSearch()
        self.reranker = Reranker()
        self.file_search = FileSearch()
        self.query_router = QueryRouter()
        self.context_builder = ContextBuilder()
        self.generator = RAGGenerator()

    def _format_history(self, messages) -> str:
        if not messages:
            return ""

        lines = []

        for message in messages:
            role = message.role.upper()
            lines.append(
                f"{role}: {message.content}"
            )

        return "\n".join(lines)

    def _extract_symbol(self, question: str) -> str | None:
        return self.query_router.extract_symbol(question)

    def _boost_exact_symbol(
        self,
        question: str,
        candidates: list[dict],
    ) -> list[dict]:

        symbol = self._extract_symbol(question)

        if symbol is None:
            return candidates

        is_class_query = self.query_router.is_class_query(
            question
        )

        symbol_lower = symbol.lower()

        for candidate in candidates:

            chunk = candidate["chunk"]

            content = chunk.content

            match = re.search(
                r"^Symbol:\s*(.+)$",
                content,
                re.MULTILINE,
            )

            if not match:
                continue

            chunk_symbol = match.group(1).strip()

            if chunk_symbol.lower() != symbol_lower:
                continue

            candidate["symbol_boost"] = 10.0

            if (
                is_class_query
                and "Symbol Type: class" in content
            ):
                candidate["symbol_boost"] = 20.0

        return candidates

    def retrieve(
        self,
        question: str,
        repository_id: int,
        retrieval_top_k: int = 30,
        final_top_k: int = 5,
    ) -> list[dict]:

        # ---------------------------------------------------------
        # Exact file existence queries
        # ---------------------------------------------------------

        file_exists = self.file_search.exists(
            query=question,
            repository_id=repository_id,
        )

        if file_exists is False:
            return []

        # ---------------------------------------------------------
        # Hybrid retrieval
        # ---------------------------------------------------------

        candidates = self.hybrid_search.search(
            query=question,
            top_k=retrieval_top_k,
            repository_id=repository_id,
        )

        if not candidates:
            return []

        # ---------------------------------------------------------
        # Exact symbol boost
        # ---------------------------------------------------------

        candidates = self._boost_exact_symbol(
            question=question,
            candidates=candidates,
        )

        for candidate in candidates:
            candidate["routing_score"] = (
                candidate["hybrid_score"]
                + candidate.get("symbol_boost", 0.0)
            )

        candidates = sorted(
            candidates,
            key=lambda item: item["routing_score"],
            reverse=True,
        )

        # ---------------------------------------------------------
        # Reranking
        # ---------------------------------------------------------

        ranked_results = self.reranker.rerank(
            query=question,
            candidates=candidates,
            top_k=final_top_k,
        )

        return ranked_results

    def answer(
        self,
        question: str,
        repository_id: int,
        retrieval_top_k: int = 30,
        final_top_k: int = 5,
        conversation_id: int | None = None,
    ) -> str:

        conversation_manager = None

        if contains_sensitive_request(question):
            return safe_security_response()

        try:
            history = ""

            if conversation_id is not None:

                conversation_manager = ConversationManager()

                conversation = (
                    conversation_manager.get_conversation(
                        conversation_id
                    )
                )

                if conversation is None:
                    raise ValueError(
                        f"Conversation {conversation_id} does not exist."
                    )

                if conversation.repository_id != repository_id:
                    raise ValueError(
                        "Conversation does not belong "
                        "to the specified repository."
                    )

                messages = (
                    conversation_manager.get_history(
                        conversation_id
                    )
                )

                history = self._format_history(messages)

                conversation_manager.save_message(
                    conversation_id=conversation_id,
                    role="user",
                    content=question,
                )

            ranked_results = self.retrieve(
                question=question,
                repository_id=repository_id,
                retrieval_top_k=retrieval_top_k,
                final_top_k=final_top_k,
            )

            context = self.context_builder.build(
                ranked_results
            )

            answer = self.generator.generate(
                question=question,
                context=context,
                history=history,
            )

            if conversation_manager is not None:

                conversation_manager.save_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=answer,
                )

            return answer

        finally:

            if conversation_manager is not None:
                conversation_manager.close()
