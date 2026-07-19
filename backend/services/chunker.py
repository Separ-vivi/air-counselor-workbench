"""文本分块器 - 段落合并 + 自然语言边界切分"""
import re
import logging

logger = logging.getLogger(__name__)


def chunk_text(text: str, size: int = 800, overlap: int = 100) -> list[str]:
    """
    将长文本切分为多个 chunk
    策略：段落合并 → 超长段落按句子拆分 → 滑动窗口重叠
    :param text: 原始文本
    :param size: 目标 chunk 大小（字符数）
    :param overlap: 重叠字符数
    :return: chunk 列表
    """
    if not text or not text.strip():
        return []

    # 1. 按段落切分
    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return []

    # 2. 合并小段落 + 按句子拆分大段落
    chunks = _merge_and_split(paragraphs, size, overlap)

    return chunks


def _split_paragraphs(text: str) -> list[str]:
    """按段落切分，优先双换行（空行），其次单换行"""
    parts = re.split(r'\n\s*\n', text)
    if len(parts) <= 1:
        parts = text.split('\n')
    return [p.strip() for p in parts if p.strip()]


def _merge_and_split(paragraphs: list[str], size: int, overlap: int) -> list[str]:
    """合并小段落，拆分大段落，带滑动重叠"""
    chunks = []
    buf = []
    buf_len = 0

    for para in paragraphs:
        if buf_len + (len(para) + 1 if buf else len(para)) <= size:
            # 段落可以放入缓冲区
            buf.append(para)
            buf_len += len(para) + (1 if buf_len > 0 else 0)
        else:
            # 缓冲区已满，先输出
            if buf:
                chunks.append('\n\n'.join(buf))
            # 单个段落超过 size → 按句子拆分
            if len(para) > size:
                sub = _split_by_sentence(para, size)
                chunks.extend(sub)
                buf = []
                buf_len = 0
            else:
                # 新段落放入缓冲区
                buf = [para]
                buf_len = len(para)

    if buf:
        chunks.append('\n\n'.join(buf))

    # 3. 添加重叠：每个 chunk 的开头包含上一个 chunk 末尾的一段文字
    if overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-overlap:]
            # 找到句子边界避免半句截断
            cut = _find_sentence_start(prev_tail)
            if cut < len(prev_tail):
                prev_tail = prev_tail[cut:]
            overlapped.append(prev_tail + '\n' + chunks[i])
        chunks = overlapped

    return chunks


def _split_by_sentence(text: str, size: int) -> list[str]:
    """按中英文句号/问号/感叹号/分号切分"""
    # 在句子边界切分
    sentences = re.split(r'(?<=[。！？；\.\!\?\;])\s*', text)
    sentences = [s for s in sentences if s.strip()]

    if not sentences:
        return _char_split(text, size)

    chunks = []
    current = ''
    for sent in sentences:
        trial = current + sent
        if len(trial) <= size:
            current = trial
        else:
            if current:
                chunks.append(current)
            current = sent
    if current:
        chunks.append(current)

    return [c for c in chunks if len(c.strip()) > 10]


def _char_split(text: str, size: int) -> list[str]:
    """纯字符切分（fallback）"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end
    return [c for c in chunks if c.strip()]


def _find_sentence_start(text: str) -> int:
    """找到文本中第一个句子起始位置（跳过开头的不完整半句）"""
    # 查找第一个句子结束符后的位置作为下一个句子的起点
    match = re.search(r'[。！？；\.\!\?\;]\s*', text)
    if match:
        return match.end()
    return 0
