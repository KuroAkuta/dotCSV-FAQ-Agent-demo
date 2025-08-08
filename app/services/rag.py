import pandas as pd
import os
import shutil
from typing import List, Dict
from fastapi import UploadFile
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.docstore.document import Document
import pathlib

# 定义数据路径 - 使用相对路径
BASE_DIR = pathlib.Path(__file__).parent.parent.parent.absolute() # 改为相对路径
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "faq.csv"
FAISS_PATH = DATA_DIR / "faq_faiss"

embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# === 载入数据 ===
def load_faq_docs(csv_path: str = CSV_PATH) -> List[Document]:
    df = pd.read_csv(csv_path)
    docs = []
    for _, row in df.iterrows():
        content = f"Q: {row['question']}\nA: {row['answer']}"
        docs.append(Document(page_content=content))
    return docs

# === 上传CSV并更新向量数据库 ===
async def upload_csv_and_update_db(file: UploadFile) -> Dict:
    """
    上传CSV文件并更新向量数据库
    
    Args:
        file: 上传的CSV文件
        
    Returns:
        包含操作结果的字典
    """
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 保存上传的文件
    temp_file_path = f"{DATA_DIR}/temp_{file.filename}"
    
    try:
        # 写入临时文件
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # 验证CSV格式是否正确（至少包含question和answer列）
        try:
            df = pd.read_csv(temp_file_path)
            if "question" not in df.columns or "answer" not in df.columns:
                os.remove(temp_file_path)
                return {"success": False, "message": "CSV文件必须包含'question'和'answer'列"}
            if df.empty:
                return {"success": False, "message": "CSV文件不包含任何数据"}
        except Exception as e:
            os.remove(temp_file_path)
            return {"success": False, "message": f"CSV文件格式错误: {str(e)}"}
        
        # 备份原始文件（如果存在）
        if os.path.exists(CSV_PATH):
            backup_path = f"{CSV_PATH}.bak"
            shutil.copy2(CSV_PATH, backup_path)
        
        # 替换原始文件
        shutil.move(temp_file_path, CSV_PATH)
        
        # 删除旧的向量数据库
        if os.path.exists(FAISS_PATH):
            shutil.rmtree(FAISS_PATH)
            # 确保目录存在
            os.makedirs(FAISS_PATH, exist_ok=True)
        
        # 创建新的向量数据库
        faq_docs = load_faq_docs(str(CSV_PATH))
        
        # 使用重建函数来更新向量数据库，并确保更新全局变量
        global vectorstore, retriever
        vectorstore, retriever = rebuild_vectorstore()
        
        return {
            "success": True, 
            "message": "CSV文件上传成功并更新了向量数据库", 
            "document_count": len(faq_docs)
        }
    
    except Exception as e:
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        print(f"❌ 处理CSV文件时出错: {str(e)}")
        return {"success": False, "message": f"处理CSV文件时出错: {str(e)}"}

# === 删除CSV文件 ===
def delete_csv() -> Dict:
    """
    删除CSV文件并清理向量数据库
    
    Returns:
        包含操作结果的字典
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(CSV_PATH):
            return {"success": False, "message": "CSV文件不存在"}
        
        # 备份文件
        backup_path = f"{CSV_PATH}.bak"
        shutil.copy2(CSV_PATH, backup_path)
        
        # 创建空的CSV文件
        with open(CSV_PATH, "w") as f:
            f.write("question,answer\n")
        
        # 完全删除向量数据库
        if os.path.exists(FAISS_PATH):
            shutil.rmtree(FAISS_PATH)
            # 确保目录存在但为空
            os.makedirs(FAISS_PATH, exist_ok=True)
        
        # 使用重建函数来更新向量数据库，并确保更新全局变量
        global vectorstore, retriever
        vectorstore, retriever = rebuild_vectorstore()
        
        return {"success": True, "message": "CSV文件已重置并清空了向量数据库"}
    
    except Exception as e:
        print(f"❌ 删除CSV文件时出错: {str(e)}")
        return {"success": False, "message": f"删除CSV文件时出错: {str(e)}"}

# === 构建Retriever ===

def initialize_vectorstore():
    """初始化或重新加载向量数据库"""
    global vectorstore, retriever
    
    # 检查FAISS目录是否存在且包含必要的文件
    if os.path.exists(FAISS_PATH) and os.path.exists(os.path.join(FAISS_PATH, "index.faiss")):
        print("🔄 加载已有向量数据库...")
        try:
            vectorstore = FAISS.load_local(
                str(FAISS_PATH),
                embedding_model,
                allow_dangerous_deserialization=True
            )
            print("✅ 成功加载向量数据库")
        except Exception as e:
            print(f"❌ 加载向量数据库失败: {str(e)}")
            # 如果加载失败，尝试重建
            return rebuild_vectorstore()
    else:
        return rebuild_vectorstore()
        
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    return vectorstore, retriever

def rebuild_vectorstore():
    """重建向量数据库"""
    global vectorstore, retriever
    
    print("⚡ 构建新的向量数据库...")
    if os.path.exists(CSV_PATH):
        faq_docs = load_faq_docs(str(CSV_PATH))
    else:
        # 如果CSV不存在，创建一个空文档
        faq_docs = [Document(page_content="这是一个空文档，用于初始化向量存储")]
        
    # 确保目录存在且有写入权限
    try:
        os.makedirs(FAISS_PATH, exist_ok=True)
        # 测试目录是否可写
        test_file = os.path.join(FAISS_PATH, "test_write.tmp")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        
        # 创建新的向量存储
        vectorstore = FAISS.from_documents(faq_docs, embedding_model)

        print("✅ 成功加载向量数据库")
        # 保存到磁盘
        vectorstore.save_local(str(FAISS_PATH))
        print(f"✅ 成功创建并保存新的向量数据库，包含 {len(faq_docs)} 个文档")
        
        # 更新检索器
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        return vectorstore, retriever
    except Exception as e:
        print(f"❌ 创建向量数据库时出错: {str(e)}")
        raise

# 初始化向量数据库
vectorstore, retriever = initialize_vectorstore()

