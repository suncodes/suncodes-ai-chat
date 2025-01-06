from langchain.text_splitter import MarkdownTextSplitter
from langchain.vectorstores import Qdrant
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from suncodes_ai_chat.suncodes_common.embedding.zhipu_embedding import ZhipuEmbeddings


class CustomQdrant:
    def __init__(self):
        self.qdrant_client = None
        self.collection_name = None
        self.vectorstore = None
        self.__init_client()
        # 初始化 OpenAI 的嵌入模型（可以换成其他模型）
        embeddings = ZhipuEmbeddings()
        self.__init_vectorstore(embeddings)

    def __init_client(self):
        # 创建 Qdrant 客户端
        self.qdrant_client = QdrantClient("http://192.168.5.25:6333")  # 如果是本地服务，默认端口是 6333
        # 创建 Qdrant 集合，用于存储向量
        self.collection_name = "langchain_collection"
        # 如果集合不存在，先创建它
        if not self.check_collection_exists(collection_name=self.collection_name):
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=2048, distance=Distance.COSINE)  # 1536 是 OpenAI 嵌入向量的维度
            )

    # 检查集合是否存在
    def check_collection_exists(self, collection_name):
        try:
            # 获取集合的详细信息
            collection_info = self.qdrant_client.get_collection(collection_name)
            return True  # 如果能够获取集合信息，则集合存在
        except Exception as e:
            if "not found" in str(e):  # 判断错误信息是否包含"not found"
                return False  # 集合不存在
            else:
                raise  # 其他错误则抛出异常

    def __init_vectorstore(self, embeddings):
        # 将这些嵌入向量存储到 Qdrant 中
        self.vectorstore = Qdrant(
            client=self.qdrant_client,
            collection_name=self.collection_name,
            embeddings=embeddings)

    def recreate_collection(self):
        """
        重建集合，如果存在，则先删除，之后重新创建一个空的
        :return:
        """
        self.qdrant_client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=2048, distance=Distance.COSINE)
        )

    def add_text(self, text: str):
        chunk_size = 500  # 每个片段包含的最大字符数
        chunk_overlap = 80  # 相邻片段的重叠字符数
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        docs = [
            Document(text)
        ]
        all_splits = text_splitter.split_documents(docs)
        all_text = []
        for all_split in all_splits:
            all_text.append(all_split.page_content)
        self.vectorstore.add_texts(all_text)

    def add_markdown_text(self, text: str):
        """
        专门拆分markdown形式的文档，对于标题，代码块，列表，表格，引用均有特殊处理
        :param text:
        :return:
        """
        text_splitter = MarkdownTextSplitter()
        docs = [Document(text)]
        all_splits = text_splitter.split_documents(docs)
        all_text = []
        for all_split in all_splits:
            all_text.append(all_split.page_content)
        self.vectorstore.add_texts(all_text)

    def get_as_retriever(self, score_threshold: float=0.5):
        ## !!! 设置相似度阈值
        return self.vectorstore.as_retriever(search_kwargs={"score_threshold": score_threshold})

if __name__ == '__main__':
    qdrant = CustomQdrant()
    qdrant.add_text("你好11")
    retriever = qdrant.get_as_retriever()

    # 定义格式化函数
    def format_docs(docs):
        return [f"Document: {doc.page_content}" for doc in docs]

    # 定义查询
    query = "What is the color of the sky?"
    # 使用检索器进行检索（retrieve 方法）
    retrieved_docs = retriever.get_relevant_documents(query)
    # 格式化检索到的文档
    formatted_docs = format_docs(retrieved_docs)

    # 输出格式化后的文档
    for doc in formatted_docs:
        print(doc)

