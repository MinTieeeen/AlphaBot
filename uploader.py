"""
Vector Store Uploader
Uploads markdown files to OpenAI Vector Store via API
"""
import os
import logging
from pathlib import Path
from typing import Dict, List

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

log = logging.getLogger(__name__)

class VectorStoreUploader:
    """Uploads markdown files to OpenAI Vector Store"""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.content_dir = Path("content")
        self.vector_store_id = os.getenv('VECTOR_STORE_ID') or None

        # Chunking configuration
        self.chunk_size = int(os.getenv('CHUNK_SIZE', '1000'))
        self.chunk_overlap = int(os.getenv('CHUNK_OVERLAP', '200'))

        # Cache for created vector store
        self._vector_store = None

    @property
    def vector_store(self):
        """Get or create vector store"""
        if self._vector_store:
            return self._vector_store

        if self.vector_store_id:
            try:
                self._vector_store = self.client.vector_stores.retrieve(self.vector_store_id)
                log.info(f"Using existing vector store: {self.vector_store_id}")
                return self._vector_store
            except Exception as e:
                log.warning(f"Could not retrieve vector store {self.vector_store_id}: {e}")

        # Create new vector store
        if not self.dry_run:
            self._vector_store = self.client.vector_stores.create(
                name="AlphaBot Knowledge Base"
            )
            self.vector_store_id = self._vector_store.id
            log.info(f"Created new vector store: {self.vector_store_id}")
            return self._vector_store

        return None

    def read_markdown_files(self) -> List[Dict]:
        """Read all markdown files from content directory"""
        files = []
        for md_file in self.content_dir.glob("*.md"):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split into chunks
            chunks = self._chunk_text(content)

            files.append({
                'path': str(md_file),
                'name': md_file.name,
                'content': content,
                'chunks': chunks
            })

        return files

    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap.

        Strategy: Split by double newlines (paragraphs),
        then combine until chunk_size is reached.
        """
        # Split by paragraph
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Check if adding this paragraph exceeds chunk size
            potential = '\n\n'.join(current_chunk + [para])

            if len(potential) > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append('\n\n'.join(current_chunk))

                # Start new chunk with overlap
                overlap_text = '\n\n'.join(current_chunk)
                if len(overlap_text) > self.chunk_overlap:
                    overlap_lines = overlap_text.split('\n')
                    overlap = []
                    for line in reversed(overlap_lines):
                        test = '\n'.join([line] + overlap)
                        if len(test) > self.chunk_overlap:
                            break
                        overlap.insert(0, line)
                    current_chunk = overlap
                else:
                    current_chunk = []

            current_chunk.append(para)

        # Don't forget last chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))

        return chunks

    def upload_file(self, file_path: str, file_name: str) -> Dict:
        """Upload a single file to vector store"""
        if self.dry_run:
            log.info(f"[DRY RUN] Would upload: {file_name}")
            return {'status': 'dry_run', 'chunks': 0}

        try:
            with open(file_path, 'rb') as f:
                result = self.client.vector_stores.vector_store_files.upload_and_poll(
                    vector_store_id=self.vector_store.id,
                    file=(
                        file_name,
                        f,
                        'text/markdown'
                    )
                )

            return {
                'status': 'completed',
                'file_id': result.id,
                'chunks': 1
            }

        except Exception as e:
            log.error(f"Failed to upload {file_name}: {e}")
            return {'status': 'error', 'error': str(e), 'chunks': 0}

    def upload_all(self) -> Dict:
        """Upload all markdown files to vector store"""
        files = self.read_markdown_files()
        log.info(f"Found {len(files)} markdown files to upload")

        # Ensure vector store exists
        vs = self.vector_store
        if not vs:
            log.warning("No vector store available (dry_run or failed creation)")
            return {'files': 0, 'chunks': 0, 'errors': 0}

        total_chunks = 0
        total_files = 0
        errors = 0

        for file_data in files:
            chunks = len(file_data['chunks'])
            result = self.upload_file(
                file_data['path'],
                file_data['name']
            )

            if result['status'] == 'completed':
                total_files += 1
                total_chunks += result.get('chunks', 0)
            else:
                errors += 1

        log.info(f"Upload complete: {total_files} files, {total_chunks} chunks, {errors} errors")

        return {
            'files': total_files,
            'chunks': total_chunks,
            'errors': errors
        }

    def get_stats(self) -> Dict:
        """Get current vector store stats"""
        if self.dry_run:
            files = self.read_markdown_files()
            return {
                'files': len(files),
                'total_chunks': sum(len(f['chunks']) for f in files)
            }

        if not self.vector_store_id:
            return {'files': 0, 'chunks': 0}

        try:
            vs = self.client.vector_stores.retrieve(self.vector_store_id)
            files = self.client.vector_stores.files.list(self.vector_store_id)

            return {
                'id': vs.id,
                'name': vs.name,
                'files': vs.file_counts,
                'created_at': vs.created_at,
                'updated_at': vs.updated_at
            }
        except Exception as e:
            log.error(f"Failed to get stats: {e}")
            return {'error': str(e)}


if __name__ == "__main__":
    uploader = VectorStoreUploader()
    result = uploader.upload_all()
    print(f"\nUploaded {result['files']} files, {result['chunks']} chunks")
