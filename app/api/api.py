from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from app.services.llm_service import generate_answer_stream
from app.services.rag import upload_csv_and_update_db, delete_csv, initialize_vectorstore

# 创建FastAPI应用实例
app = FastAPI(title="FAQ RAG Agent")

# 配置CORS中间件，允许所有来源的请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

# 请求体结构
class Question(BaseModel):
    input: str

@app.post("/ask")
async def ask_stream(question: Question):
    """
    处理用户问题并返回流式回答

    Args:
        question: 包含用户输入的请求体

    Returns:
        StreamingResponse: 流式响应对象
    """
    user_input = question.input
    answer_generator = await generate_answer_stream(user_input)
    return StreamingResponse(answer_generator, media_type="text/plain")

@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """
    上传CSV文件并更新向量数据库
    
    Args:
        file: 上传的CSV文件
        
    Returns:
        JSONResponse: 包含操作结果的JSON响应
    """
    # 检查文件类型
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="只接受CSV文件")
    
    # 调用业务逻辑处理上传
    result = await upload_csv_and_update_db(file)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return JSONResponse(content=result)

@app.delete("/delete-csv")
async def delete_csv_endpoint():
    """
    删除CSV文件并清理向量数据库
    
    Returns:
        JSONResponse: 包含操作结果的JSON响应
    """
    result = delete_csv()
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    
    return JSONResponse(content=result)

@app.post("/reload-vectordb")
async def reload_vector_database():
    """
    重新加载向量数据库
    
    Returns:
        JSONResponse: 包含操作结果的JSON响应
    """
    try:
        # 确保全局变量被更新
        initialize_vectorstore()
        return JSONResponse(content={"success": True, "message": "向量数据库已成功重新加载"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新加载向量数据库时出错: {str(e)}")