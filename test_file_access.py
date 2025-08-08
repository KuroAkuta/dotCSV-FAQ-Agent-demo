import os
import pathlib

def check_file_access(file_path):
    print(f"检查文件: {file_path}")
    print(f"文件存在: {os.path.exists(file_path)}")
    print(f"文件可读: {os.access(file_path, os.R_OK)}")
    print(f"文件大小: {os.path.getsize(file_path) if os.path.exists(file_path) else 0} 字节")

if __name__ == "__main__":
    faiss_path = pathlib.Path("data/faq_faiss/index.faiss")
    pkl_path = pathlib.Path("data/faq_faiss/index.pkl")

    print("检查FAISS文件:")
    check_file_access(faiss_path)

    print("\n检查PKL文件:")
    check_file_access(pkl_path)
