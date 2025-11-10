from langchain_community.embeddings import HuggingFaceEmbeddings

def get_embeddings():
    model_name = "Alibaba-NLP/gte-multilingual-base"
    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"trust_remote_code": True}
    )
    return embeddings

embeddings = get_embeddings()

__all__ = ["embeddings", "get_embeddings"]