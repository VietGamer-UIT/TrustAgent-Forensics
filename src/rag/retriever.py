"""
TrustAgent.Forensics — Legal RAG Retriever (Phase 3.5)

Nhiệm vụ: Lấy đúng văn bản luật từ kho lưu trữ dựa trên ScenarioType.

Quyết định kiến trúc — ChromaDB vs pgvector:
────────────────────────────────────────────
• ChromaDB (ĐÃ CHỌN cho RAG Module):
  - Embedded, zero config, chạy trong process — không cần server
  - Phù hợp cho corpus nhỏ (< 100 docs, < 1MB): legal documents
  - Dùng được trong dev/test không cần Docker/PostgreSQL
  - Khi Phase 4 lên PostgreSQL, KHÔNG cần migrate RAG vì hai concerns khác nhau

• pgvector (Dùng cho Phase 4 — Audit Trail):
  - Tích hợp vào PostgreSQL chính của hệ thống
  - Phù hợp cho audit trail lớn, cần ACID, JOIN với dữ liệu quan hệ
  - Sẽ implement ở Phase 4 cho việc tìm kiếm lịch sử giao dịch

Kết luận: Hai công cụ phục vụ hai mục đích khác nhau → dùng cả hai.

Fallback Strategy (3 tầng):
  1. ChromaDB với semantic search (nếu cài chromadb)
  2. Keyword-based search trong memory (luôn hoạt động)
  3. Hardcoded defaults (không bao giờ fail)
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Đường dẫn tới thư mục chứa văn bản luật
_LEGAL_DATA_DIR = Path(__file__).parent / "legal_data"

# Default thresholds — fallback khi RAG fail hoàn toàn
DEFAULT_THRESHOLDS: dict[str, dict[str, int]] = {
    "vn_payment": {
        "VN_CASH_THRESHOLD": 20_000_000,
    },
    "kr_tax_refund": {
        "KR_MIN_RECEIPT_AMOUNT": 30_000,
        "KR_CUSTOMS_CHECK_THRESHOLD": 75_000,
    },
}

# Map ScenarioType → file luật tương ứng
_SCENARIO_TO_FILE: dict[str, str] = {
    "vn_payment": "VN_tax_law.md",
    "kr_tax_refund": "KR_refund_law.md",
}


class LegalRetriever:
    """
    Lấy văn bản luật phù hợp từ kho dữ liệu dựa trên ScenarioType.

    Chiến lược fallback 3 tầng:
    1. ChromaDB semantic search (nếu đã cài: pip install chromadb)
    2. Keyword-based in-memory search (luôn hoạt động)
    3. Trả về toàn bộ document nếu không tìm được chunk phù hợp

    Ví dụ:
        retriever = LegalRetriever()
        text = retriever.get_legal_text("vn_payment")
        # → "...Ngưỡng thanh toán tiền mặt tối đa: 20,000,000 VNĐ..."
    """

    def __init__(self, data_dir: Path | str | None = None) -> None:
        self._data_dir = Path(data_dir) if data_dir else _LEGAL_DATA_DIR
        self._docs: dict[str, str] = {}          # scenario → full document text
        self._collection = None                   # ChromaDB collection (optional)
        self._chromadb_available = False

        self._load_all_docs()
        self._try_init_chromadb()

    # -----------------------------------------------------------------------
    # Khởi tạo
    # -----------------------------------------------------------------------

    def _load_all_docs(self) -> None:
        """Load tất cả markdown files từ legal_data/ vào memory."""
        for scenario, filename in _SCENARIO_TO_FILE.items():
            filepath = self._data_dir / filename
            if filepath.exists():
                self._docs[scenario] = filepath.read_text(encoding="utf-8")
                logger.info(f"[RAG] Loaded legal doc: {filename} ({len(self._docs[scenario])} chars)")
            else:
                logger.warning(f"[RAG] Legal doc not found: {filepath}")

    def _try_init_chromadb(self) -> None:
        """Thử khởi tạo ChromaDB. Nếu fail → dùng keyword search."""
        try:
            import chromadb  # noqa: F401 (optional dependency)
            from chromadb.config import Settings

            client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(self._data_dir / ".chroma_cache"),
                anonymized_telemetry=False,
            ))
            self._collection = client.get_or_create_collection(
                name="legal_documents",
                metadata={"hnsw:space": "cosine"},
            )
            self._index_docs_to_chromadb()
            self._chromadb_available = True
            logger.info("[RAG] ChromaDB initialized successfully")
        except ImportError:
            logger.info("[RAG] ChromaDB not installed → using keyword-based retrieval (OK for dev)")
        except Exception as e:
            logger.warning(f"[RAG] ChromaDB init failed: {e} → using keyword-based retrieval")

    def _index_docs_to_chromadb(self) -> None:
        """Index các legal docs vào ChromaDB với chunking đơn giản."""
        if self._collection is None:
            return

        # Kiểm tra đã index chưa
        if self._collection.count() > 0:
            return

        chunks = []
        metadatas = []
        ids = []

        for scenario, doc_text in self._docs.items():
            # Chunk theo paragraph (split by double newline)
            paragraphs = [p.strip() for p in doc_text.split("\n\n") if len(p.strip()) > 50]
            for i, para in enumerate(paragraphs):
                chunks.append(para)
                metadatas.append({"scenario": scenario, "chunk_id": i})
                ids.append(f"{scenario}_{i}")

        if chunks:
            self._collection.add(documents=chunks, metadatas=metadatas, ids=ids)
            logger.info(f"[RAG] Indexed {len(chunks)} chunks to ChromaDB")

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def get_legal_text(self, scenario_type: str, n_chunks: int = 5) -> str:
        """
        Lấy văn bản luật liên quan đến scenario_type.

        Args:
            scenario_type: "vn_payment" | "kr_tax_refund"
            n_chunks: Số chunks tối đa trả về (chỉ dùng khi ChromaDB available)

        Returns:
            Đoạn văn bản luật liên quan, hoặc chuỗi rỗng nếu không tìm thấy.
        """
        if scenario_type not in self._docs:
            logger.warning(f"[RAG] No legal doc for scenario: {scenario_type}")
            return ""

        # Tầng 1: ChromaDB semantic search
        if self._chromadb_available and self._collection:
            try:
                results = self._collection.query(
                    query_texts=[scenario_type],
                    n_results=min(n_chunks, self._collection.count()),
                    where={"scenario": scenario_type},
                )
                if results["documents"] and results["documents"][0]:
                    return "\n\n".join(results["documents"][0])
            except Exception as e:
                logger.warning(f"[RAG] ChromaDB query failed: {e} → fallback to keyword")

        # Tầng 2 & 3: Trả về toàn bộ document (đủ nhỏ để fit trong LLM context)
        return self._docs[scenario_type]

    def get_threshold_json(self, scenario_type: str) -> str:
        """
        Lấy đoạn JSON metadata chứa threshold từ văn bản luật.
        Dùng regex để extract JSON block từ markdown.

        Returns:
            JSON string hoặc "" nếu không tìm thấy.
        """
        text = self._docs.get(scenario_type, "")
        if not text:
            return ""

        # Tìm JSON block trong markdown code fence
        match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def is_available(self, scenario_type: str) -> bool:
        """Kiểm tra có legal doc cho scenario này không."""
        return scenario_type in self._docs
