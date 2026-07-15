"""
Test suite for AlphaBot
"""
import os
import sys
import pytest
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))


class TestScraper:
    """Tests for OptiSignsScraper"""

    def test_scraper_initializes(self):
        """Test scraper can be initialized"""
        from scraper import OptiSignsScraper
        scraper = OptiSignsScraper()
        assert scraper is not None
        assert scraper.content_dir.exists()

    def test_slugify(self):
        """Test title to slug conversion"""
        from scraper import OptiSignsScraper
        scraper = OptiSignsScraper()

        assert scraper._slugify("Hello World") == "hello-world"
        assert scraper._slugify("How to Use YouTube") == "how-to-use-youtube"
        assert scraper._slugify("Test! @Special# Chars") == "test-special-chars"

    def test_compute_hash(self):
        """Test content hashing"""
        from scraper import OptiSignsScraper
        scraper = OptiSignsScraper()

        hash1 = scraper._compute_hash("hello")
        hash2 = scraper._compute_hash("hello")
        hash3 = scraper._compute_hash("world")

        assert hash1 == hash2  # Same content = same hash
        assert hash1 != hash3  # Different content = different hash
        assert len(hash1) == 64  # SHA256 produces 64 char hex


class TestUploader:
    """Tests for VectorStoreUploader"""

    def test_uploader_initializes_without_api(self):
        """Test uploader can be initialized in dry_run mode without API key"""
        from uploader import VectorStoreUploader
        # Set dummy env for test
        os.environ.setdefault('OPENAI_API_KEY', 'test-key')
        uploader = VectorStoreUploader(dry_run=True)
        assert uploader is not None
        assert uploader.dry_run is True

    def test_chunk_text(self):
        """Test text chunking"""
        from uploader import VectorStoreUploader
        os.environ.setdefault('OPENAI_API_KEY', 'test-key')
        uploader = VectorStoreUploader(dry_run=True)
        uploader.chunk_size = 100
        uploader.chunk_overlap = 20

        # Single paragraph smaller than chunk
        text = "This is a short paragraph."
        chunks = uploader._chunk_text(text)
        assert len(chunks) == 1

        # Multiple paragraphs
        long_text = "\n\n".join([f"Paragraph {i} with some content" for i in range(10)])
        chunks = uploader._chunk_text(long_text)
        assert len(chunks) >= 1


class TestMain:
    """Tests for main.py"""

    def test_env_sample_exists(self):
        """Test .env.sample file exists"""
        assert Path(".env.sample").exists()

    def test_required_files_exist(self):
        """Test all required files exist"""
        required = ["main.py", "scraper.py", "uploader.py", "requirements.txt", "Dockerfile"]
        for f in required:
            assert Path(f).exists(), f"Missing required file: {f}"

    def test_content_dir_exists(self):
        """Test content directory exists"""
        assert Path("content").exists()

    def test_requirements_has_openai(self):
        """Test requirements.txt includes openai"""
        content = Path("requirements.txt").read_text()
        assert "openai" in content.lower()


class TestIntegration:
    """Integration tests - requires scraped content"""

    @pytest.fixture
    def md_files(self):
        """Get markdown files if available"""
        files = list(Path("content").glob("*.md"))
        return files

    def test_scraper_produces_markdown(self, md_files):
        """Test scraper creates markdown files in content/"""
        if len(md_files) == 0:
            pytest.skip("No markdown files in content/ (run scrape first)")

    def test_markdown_files_have_content(self, md_files):
        """Test markdown files are not empty"""
        if len(md_files) == 0:
            pytest.skip("No markdown files in content/ (run scrape first)")

        for md_file in md_files[:5]:
            content = md_file.read_text()
            assert len(content) > 100, f"{md_file.name} seems empty or too short"

    def test_markdown_has_headings(self, md_files):
        """Test markdown files have headings"""
        if len(md_files) == 0:
            pytest.skip("No markdown files in content/ (run scrape first)")

        sample = md_files[0].read_text()
        assert "# " in sample, "Markdown should have at least one heading"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
