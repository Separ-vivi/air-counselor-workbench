"""文本分块器 - 按段落/句号优先切，fallback 按字符切"""
import re
import logging

logger = logging.getLogger(__name__)


def chunk_text(text: str, size: int = 500, overlap: int = 50) -> list[str]:
    """
    将长文本切分为多个 chunk
    优先级：段落切 > 句号切 > 字符切
    :param text: 原始文本
    :param size: 目标 chunk 大小（字符数）
    :param overlap: 重叠字符数
    :return: chunk 列表
    """
    if not text or not text.strip():
        return []

    # 1. 先按段落切（双换行 或 单换行+缩进）
    paragraphs = _split_paragraphs(text)

    # 2. 合并过小的段落，拆分过大的段落
    chunks = _merge_and_split(paragraphs, size, overlap)

    if not chunks:
        # fallback: 纯字符切
        chunks = _char_split(text, size, overlap)

    return chunks


def _split_paragraphs(text: str) -> list[str]:
    """按段落切分，保留段落完整性"""
    # 先按双换行（空行）分
    parts = re.split(r'\n\s*\n', text)
    # 如果段落太少，按单换行分
    if len(parts) <= 1:
        parts = text.split('\n')
    # 过滤空段落
    return [p.strip() for p in parts if p.strip()]


def _merge_and_split(paragraphs: list[str], size: int, overlap: int) -> list[str]:
    """合并小段落，拆分大段落"""
    chunks = []
    current = []

    for para in paragraphs:
        # 单个段落超过 size → 按句号拆分
        if len(para) > size:
            # 先把当前积累的段落合入
            if current:
                chunks.append('\n'.join(current))
                current = []
            # 按句号拆分大段落
            sub_chunks = _split_by_sentence(para, size, overlap)
            chunks.extend(sub_chunks)
        else:
            # 尝试合并到当前 chunk
            trial = '\n'.join(current + [para])
            if len(trial) <= size:
                current.append(para)
            else:
                # 当前 chunk 已满，保存并开始新 chunk
                if current:
                    chunks.append('\n'.join(current))
                # overlap: 保留最后一个段落
                current = [para] if not current else [current[-1], para] if len(current) > 0 and len('\n'.join([current[-1], para])) <= size else [para]

    if current:
        chunks.append('\n'.join(current))

    return chunks


def _split_by_sentence(text: str, size: int, overlap: int) -> list[str]:
    """按中英文句号/问号/感叹号切分，再合并"""
    # 按句子边界切
    sentences = re.split(r'(?<=[。！？\.!?])\s*', text)
    sentences = [s for s in sentences if s.strip()]

    if not sentences:
        return _char_split(text, size, overlap)

    chunks = []
    current = ''
    for sent in sentences:
        trial = current + sent
        if len(trial) <= size:
            current = trial
        else:
            if current:
                chunks.append(current)
            # overlap
            if overlap > 0 and current:
                overlap_text = current[-overlap:]
                current = overlap_text + sent
            else:
                current = sent
    if current:
        chunks.append(current)

    # 过滤过短的
    return [c for c in chunks if len(c.strip()) > 10]


def _char_split(text: str, size: int, overlap: int) -> list[str]:
    """纯字符切分（fallback）"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap if end < len(text) else end
    return [c for c in chunks if c.strip()]
