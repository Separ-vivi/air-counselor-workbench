"""文件解析器 - 支持 docx/pdf/txt，纯本地解析，不调外部 API"""
import os
import logging

logger = logging.getLogger(__name__)

MAX_CHARS = 50000  # 超长文档截断阈值


def parse(file_path: str) -> str:
    """
    解析文件内容为纯文本
    :param file_path: 文件路径
    :return: 解析后的文本
    :raises: ValueError 不支持的文件类型
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.docx':
        text = _parse_docx(file_path)
    elif ext == '.pdf':
        text = _parse_pdf(file_path)
    elif ext == '.txt':
        text = _parse_txt(file_path)
    else:
        raise ValueError(f'不支持的文件类型: {ext}，仅支持 .docx/.pdf/.txt')

    # 超长截断
    if len(text) > MAX_CHARS:
        logger.warning(f"文档超长({len(text)}字)，截断到 {MAX_CHARS} 字: {file_path}")
        text = text[:MAX_CHARS]

    return text


def _parse_docx(file_path: str) -> str:
    """python-docx 解析 .docx"""
    from docx import Document
    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return '\n'.join(paragraphs)


def _parse_pdf(file_path: str) -> str:
    """pdfplumber 解析 .pdf"""
    import pdfplumber
    texts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                texts.append(text)
    return '\n'.join(texts)


def _parse_txt(file_path: str) -> str:
    """txt 解析，自动探测 utf-8/gbk"""
    # 尝试 utf-8
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        pass
    # 回退 gbk
    try:
        with open(file_path, 'r', encoding='gbk') as f:
            return f.read()
    except UnicodeDecodeError:
        pass
    # 最后尝试 latin-1（不会失败）
    with open(file_path, 'r', encoding='latin-1') as f:
        return f.read()
