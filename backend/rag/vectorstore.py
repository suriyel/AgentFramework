"""
RAG Vector Store - Chroma 集成
用于领域知识检索
"""
from typing import List, Dict, Any, Optional
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from loguru import logger
from backend.config.settings import settings
import os


class KnowledgeBase:
    """知识库管理"""

    def __init__(self):
        """初始化知识库"""
        self.persist_directory = settings.CHROMA_PERSIST_DIR
        self.collection_name = settings.CHROMA_COLLECTION_NAME

        # 确保目录存在
        os.makedirs(self.persist_directory, exist_ok=True)

        # 初始化 Embedding 模型
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},  # 使用 GPU: 'cuda'
            encode_kwargs={'normalize_embeddings': True}
        )

        # 初始化 Vector Store
        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

        logger.success("Knowledge base initialized")

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> List[str]:
        """
        添加文档到知识库

        Args:
            documents: 文档内容列表
            metadatas: 文档元数据列表
            chunk_size: 分块大小
            chunk_overlap: 分块重叠

        Returns:
            文档 ID 列表
        """
        try:
            # 文本分块
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
            )

            # 创建 Document 对象
            docs = []
            for idx, content in enumerate(documents):
                metadata = metadatas[idx] if metadatas and idx < len(metadatas) else {}
                chunks = text_splitter.split_text(content)

                for chunk_idx, chunk in enumerate(chunks):
                    docs.append(Document(
                        page_content=chunk,
                        metadata={
                            **metadata,
                            "chunk_index": chunk_idx,
                            "source_index": idx
                        }
                    ))

            # 添加到向量数据库
            ids = self.vectorstore.add_documents(docs)

            logger.info(f"Added {len(docs)} document chunks to knowledge base")
            return ids

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise

    def search(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        搜索相关文档

        Args:
            query: 查询文本
            k: 返回文档数量
            filter_metadata: 元数据过滤条件

        Returns:
            相关文档列表
        """
        try:
            if filter_metadata:
                results = self.vectorstore.similarity_search(
                    query,
                    k=k,
                    filter=filter_metadata
                )
            else:
                results = self.vectorstore.similarity_search(query, k=k)

            logger.debug(f"Retrieved {len(results)} documents for query: {query[:50]}...")
            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def search_with_score(
        self,
        query: str,
        k: int = 5,
        score_threshold: float = 0.5
    ) -> List[tuple[Document, float]]:
        """
        带相似度分数的搜索

        Args:
            query: 查询文本
            k: 返回文档数量
            score_threshold: 分数阈值

        Returns:
            (文档, 分数) 元组列表
        """
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k)

            # 过滤低分结果
            filtered_results = [
                (doc, score) for doc, score in results
                if score >= score_threshold
            ]

            logger.debug(f"Retrieved {len(filtered_results)} documents with score >= {score_threshold}")
            return filtered_results

        except Exception as e:
            logger.error(f"Search with score failed: {e}")
            return []

    def delete_by_metadata(self, filter_metadata: Dict[str, Any]) -> bool:
        """根据元数据删除文档"""
        try:
            # Chroma doesn't support delete by filter directly
            # You need to get IDs first, then delete
            logger.warning("Delete by metadata not fully implemented")
            return False
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False

    def get_collection_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        try:
            collection = self.vectorstore._collection
            count = collection.count()

            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}


# 全局知识库实例
knowledge_base = KnowledgeBase()
