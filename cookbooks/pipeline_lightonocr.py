import base64
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pypdfium2 as pdfium
import io
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

ENDPOINT = "http://localhost:9090/v1/chat/completions"
MODEL = "LightOnOCR-2-1B"
MAX_WORKERS = 8
REQUEST_TIMEOUT = 120  # 每个请求的超时时间（秒）

# 线程本地存储，每个线程使用独立的 session
_thread_local = threading.local()


def get_thread_session():
    """获取当前线程的独立 session（避免多线程竞争）"""
    if not hasattr(_thread_local, 'session') or _thread_local.session is None:
        _thread_local.session = create_session()
    return _thread_local.session


def create_session():
    """创建带有连接池和重试机制的 session"""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.1,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(
        pool_connections=MAX_WORKERS,
        pool_maxsize=MAX_WORKERS * 2,
        max_retries=retry
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


# 全局 session
_session = None


def get_session():
    """获取或创建全局 session"""
    global _session
    if _session is None:
        _session = create_session()
    return _session

def pdf_page_to_image_base64(page):
    """将 PDF 页面渲染为 base64 编码的 PNG 图片"""
    pil_image = page.render(scale=2.77).to_pil()  # 200 DPI
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def ocr_image(page_num: int, image_base64: str) -> str:
    """调用 OCR API 识别图片中的文字（使用连接池）"""
    session = get_thread_session()
    payload = {
        "model": MODEL,
        "messages": [{
            "role": "user",
            "content": [{
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_base64}"}
            }]
        }],
        "max_tokens": 4096,
        "temperature": 0.2,
        "top_p": 0.9,
    }
    # 添加超时和错误处理
    try:
        print(f"[DEBUG] 第 {page_num + 1} 页: 开始发送请求...")
        response = session.post(ENDPOINT, json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        print(f"[DEBUG] 第 {page_num + 1} 页: 收到响应，状态码 {response.status_code}")
        return response.json()['choices'][0]['message']['content']
    except requests.Timeout:
        print(f"[DEBUG] 第 {page_num + 1} 页: 请求超时")
        raise Exception(f"请求超时（{REQUEST_TIMEOUT}秒）")
    except requests.RequestException as e:
        print(f"[DEBUG] 第 {page_num + 1} 页: 请求失败 - {e}")
        raise Exception(f"请求失败: {e}")
    except (KeyError, IndexError) as e:
        print(f"[DEBUG] 第 {page_num + 1} 页: 响应解析失败 - {e}")
        raise Exception(f"响应解析失败: {e}")


def pdf_to_md(pdf_path: str, output_md_path: str):
    """将 PDF 的所有页面转换为单个 Markdown 文件（并发处理）"""
    # 读取本地 PDF 文件
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()

    # 打开 PDF
    pdf = pdfium.PdfDocument(pdf_data)
    total_pages = len(pdf)

    print(f"PDF 共 {total_pages} 页，开始并发处理（{MAX_WORKERS} 线程）...")

    # 预先渲染所有页面为 base64
    print("正在渲染所有页面...")
    pages_data = []
    for page_num in range(total_pages):
        page = pdf[page_num]
        image_base64 = pdf_page_to_image_base64(page)
        pages_data.append((page_num, image_base64))

    print(f"渲染完成，开始 OCR 识别...")

    # 使用线程池并发处理 OCR
    results = {}
    failed_pages = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务
        future_to_page = {
            executor.submit(ocr_image, page_num, img_b64): page_num
            for page_num, img_b64 in pages_data
        }

        # 收集结果
        completed = 0
        for future in as_completed(future_to_page):
            page_num = future_to_page[future]
            try:
                text = future.result()
                results[page_num] = text
                completed += 1
                print(f"进度: {completed}/{total_pages} 页完成 (第 {page_num + 1} 页)")
            except Exception as e:
                error_msg = f"[处理失败: {e}]"
                print(f"第 {page_num + 1} 页处理失败: {e}")
                results[page_num] = error_msg
                failed_pages.append(page_num + 1)

    # 按页面顺序组合内容
    all_content = []
    for page_num in range(total_pages):
        all_content.append(f"\n\n## Page {page_num + 1}\n\n")
        all_content.append(results[page_num])

    # 合并所有内容
    combined_text = "".join(all_content)

    # 保存带页面分隔符的版本
    output_path_with_separators = output_md_path.replace(".md", "_with_separators.md")
    Path(output_path_with_separators).write_text(combined_text, encoding="utf-8")
    print(f"带分隔符版本已保存到 {output_path_with_separators}")

    # 保存不带页面分隔符的版本
    clean_content = []
    for i, item in enumerate(all_content):
        # 跳过页面分隔符（偶数索引是分隔符）
        if i % 2 == 1:
            clean_content.append(item)
    clean_text = "".join(clean_content)
    Path(output_md_path).write_text(clean_text, encoding="utf-8")
    print(f"无分隔符版本已保存到 {output_md_path}")

    # 汇总失败页面
    if failed_pages:
        print(f"\n警告: 以下页面处理失败: {failed_pages}")

# # 示例调用
pdf_path = "/home/lz/repo/onn_x/test1.pdf"
output_md_path = "/home/lz/repo/onn_x/test1.md"
pdf_to_md(pdf_path, output_md_path)
