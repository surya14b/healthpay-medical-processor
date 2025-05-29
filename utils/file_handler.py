"""
File handling utilities for HealthPay claim processor
"""

import os
import shutil
import tempfile
from typing import Dict, Any, List
from fastapi import UploadFile
import logging
import hashlib
from pathlib import Path
import PyPDF2

logger = logging.getLogger(__name__)

class FileHandler:
    """
    Utility class for handling file operations
    """
    
    def __init__(self, upload_dir: str = None):
        self.upload_dir = upload_dir or tempfile.mkdtemp(prefix="healthpay_")
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg'}
        
        # Ensure upload directory exists
        os.makedirs(self.upload_dir, exist_ok=True)
        logger.info(f"FileHandler initialized with upload_dir: {self.upload_dir}")
    
    async def save_uploaded_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        Save uploaded file and return file information
        """
        try:
            # Validate file
            await self._validate_file(file)
            
            # Generate safe filename
            safe_filename = self._generate_safe_filename(file.filename)
            file_path = os.path.join(self.upload_dir, safe_filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Generate file hash for integrity
            file_hash = self._calculate_file_hash(file_path)
            
            # Get file info
            file_info = {
                "filename": file.filename,
                "safe_filename": safe_filename,
                "file_path": file_path,
                "file_size": os.path.getsize(file_path),
                "file_hash": file_hash,
                "content_type": file.content_type,
            }
            
            # Add content preview for text extraction
            if file.filename.lower().endswith('.pdf'):
                file_info["content_preview"] = await self._get_pdf_preview(file_path)
            
            logger.info(f"Successfully saved file: {file.filename} as {safe_filename}")
            return file_info
            
        except Exception as e:
            logger.error(f"Error saving file {file.filename}: {str(e)}")
            raise
    
    async def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file"""
        
        # Check file size
        if hasattr(file, 'size') and file.size > self.max_file_size:
            raise ValueError(f"File {file.filename} exceeds maximum size of {self.max_file_size} bytes")
        
        # Check file extension
        if file.filename:
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in self.allowed_extensions:
                raise ValueError(f"File type {file_ext} not allowed. Allowed types: {self.allowed_extensions}")
        
        # Basic content type validation
        if file.content_type and not any(ct in file.content_type.lower() 
                                       for ct in ['pdf', 'image']):
            logger.warning(f"Unexpected content type: {file.content_type}")
    
    def _generate_safe_filename(self, filename: str) -> str:
        """Generate a safe filename to prevent path traversal attacks"""
        if not filename:
            filename = "unnamed_file"
        
        # Extract extension
        path = Path(filename)
        name = path.stem
        ext = path.suffix
        
        # Clean filename
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        
        # Add timestamp to avoid conflicts
        import time
        timestamp = int(time.time())
        
        return f"{safe_name}_{timestamp}{ext}"
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file for integrity verification"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    async def _get_pdf_preview(self, file_path: str) -> str:
        """Get a preview of PDF content for classification"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                if len(pdf_reader.pages) > 0:
                    # Get first page text as preview
                    first_page = pdf_reader.pages[0]
                    preview_text = first_page.extract_text()[:500]  # First 500 chars
                    return preview_text
                return ""
        except Exception as e:
            logger.warning(f"Could not extract PDF preview: {str(e)}")
            return ""
    
    def cleanup_file(self, file_path: str) -> bool:
        """Clean up a specific file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {str(e)}")
            return False
    
    def cleanup_all(self) -> None:
        """Clean up all files in upload directory"""
        try:
            if os.path.exists(self.upload_dir):
                shutil.rmtree(self.upload_dir)
                logger.info(f"Cleaned up upload directory: {self.upload_dir}")
        except Exception as e:
            logger.error(f"Error cleaning up upload directory: {str(e)}")
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a file"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            stat = os.stat(file_path)
            return {
                "file_path": file_path,
                "file_size": stat.st_size,
                "created_time": stat.st_ctime,
                "modified_time": stat.st_mtime,
                "exists": True
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {str(e)}")
            return {"exists": False, "error": str(e)}
    
    def list_uploaded_files(self) -> List[Dict[str, Any]]:
        """List all files in upload directory"""
        files = []
        try:
            if os.path.exists(self.upload_dir):
                for filename in os.listdir(self.upload_dir):
                    file_path = os.path.join(self.upload_dir, filename)
                    if os.path.isfile(file_path):
                        file_info = self.get_file_info(file_path)
                        file_info["filename"] = filename
                        files.append(file_info)
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
        
        return files
