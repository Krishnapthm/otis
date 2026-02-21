"""
Core Hashing Utilities for PDF Ingestion Pipeline

Provides memory-safe hashing functions for:
- File-level deduplication (streaming file hash)
- Content-level deduplication (normalized text hash)
"""

import hashlib
import unicodedata
import re
from typing import IO

BUFFER_SIZE = 8192  # 8KB chunks for streaming


def compute_file_hash_streaming(file_path: str) -> str:
    """
    Compute SHA-256 hash of a file using chunked reads.
    
    Memory-safe: never loads the full file into RAM.
    
    Args:
        file_path: Path to the file on disk
        
    Returns:
        64-character lowercase hex string (SHA-256)
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(BUFFER_SIZE):
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_file_hash_from_stream(file_obj: IO[bytes]) -> str:
    """
    Compute SHA-256 hash from a file-like object using chunked reads.
    
    Memory-safe: reads in 8KB chunks.
    
    Args:
        file_obj: File-like object opened in binary mode
        
    Returns:
        64-character lowercase hex string (SHA-256)
    """
    sha256 = hashlib.sha256()
    while chunk := file_obj.read(BUFFER_SIZE):
        sha256.update(chunk)
    return sha256.hexdigest()


def normalize_text(text: str) -> str:
    """
    Normalize text for consistent content hashing.
    
    Applies:
    - Unicode NFC normalization
    - Lowercase conversion
    - Whitespace collapse (multiple spaces/newlines → single space)
    - Zero-width character removal (ZWSP, ZWNJ, ZWJ, BOM)
    - Strip leading/trailing whitespace
    
    Args:
        text: Raw text content
        
    Returns:
        Normalized text suitable for hashing
    """
    # Unicode normalization (canonical decomposition + composition)
    text = unicodedata.normalize("NFC", text)
    
    # Lowercase for case-insensitive matching
    text = text.lower()
    
    # Collapse all whitespace (spaces, tabs, newlines) to single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove zero-width characters and BOM
    text = re.sub(r'[\u200b-\u200d\ufeff\u00ad]', '', text)
    
    # Strip leading/trailing
    return text.strip()


def compute_content_hash(text: str) -> str:
    """
    Compute SHA-256 hash of normalized text content.
    
    Two documents with the same textual content (after normalization)
    will produce the same content hash, even if the PDFs differ.
    
    Args:
        text: Raw text content (will be normalized)
        
    Returns:
        64-character lowercase hex string (SHA-256)
    """
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
