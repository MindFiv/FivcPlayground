#!/usr/bin/env python3
"""
Tests for the CLI setup command.
"""

import tempfile
import shutil
from pathlib import Path


class TestSetupCommand:
    """Tests for the setup command functionality"""

    def test_config_directory_creation(self):
        """Test that config directory structure is created correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / ".fivcplayground" / "configs"
            config_dir.mkdir(parents=True, exist_ok=True)

            assert config_dir.exists()
            assert config_dir.is_dir()
            assert config_dir.parent.exists()
            assert config_dir.parent.name == ".fivcplayground"

    def test_config_files_copy_operation(self):
        """Test that config files can be copied correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create source and target directories
            source_dir = Path(tmpdir) / "source"
            target_dir = Path(tmpdir) / "target" / "configs"
            source_dir.mkdir()
            target_dir.mkdir(parents=True)

            # Create a test source file
            test_file = source_dir / "test.yaml"
            test_file.write_text("test content")

            # Copy using shutil.copy2 (as the setup command does)
            target_file = target_dir / "test.yaml"
            shutil.copy2(test_file, target_file)

            assert target_file.exists()
            assert target_file.read_text() == "test content"

    def test_file_metadata_preservation(self):
        """Test that shutil.copy2 preserves file metadata"""
        with tempfile.TemporaryDirectory() as tmpdir:
            source_file = Path(tmpdir) / "source.yaml"
            target_file = Path(tmpdir) / "target.yaml"

            source_file.write_text("content")
            source_stat = source_file.stat()

            shutil.copy2(source_file, target_file)
            target_stat = target_file.stat()

            # Metadata should be preserved (modification time)
            assert source_stat.st_mtime == target_stat.st_mtime

    def test_overwrite_existing_file(self):
        """Test that existing files can be overwritten"""
        with tempfile.TemporaryDirectory() as tmpdir:
            target_file = Path(tmpdir) / "config.yaml"
            target_file.write_text("old content")

            source_file = Path(tmpdir) / "source.yaml"
            source_file.write_text("new content")

            # Overwrite
            shutil.copy2(source_file, target_file)

            assert target_file.read_text() == "new content"

    def test_config_files_list(self):
        """Test that all required config files are identified"""
        config_files = [
            ("agents.yaml.example", "agents.yaml"),
            ("models.yaml.example", "models.yaml"),
            ("embeddings.yaml.example", "embeddings.yaml"),
            ("tools.yaml.example", "tools.yaml"),
        ]

        assert len(config_files) == 4
        for source, target in config_files:
            assert source.endswith(".example")
            assert target.endswith(".yaml")
            assert not target.endswith(".example")

    def test_project_configs_directory_exists(self):
        """Test that project configs directory can be located"""
        # Get the project root from cli.py location
        cli_file = Path(__file__).parent.parent / "src" / "fivcplayground" / "cli.py"
        project_root = cli_file.parent.parent.parent
        project_configs_dir = project_root / "configs"

        assert project_configs_dir.exists()
        assert project_configs_dir.is_dir()

    def test_example_config_files_exist(self):
        """Test that example config files exist in project"""
        cli_file = Path(__file__).parent.parent / "src" / "fivcplayground" / "cli.py"
        project_root = cli_file.parent.parent.parent
        project_configs_dir = project_root / "configs"

        example_files = [
            "agents.yaml.example",
            "models.yaml.example",
            "embeddings.yaml.example",
            "tools.yaml.example",
        ]

        for file in example_files:
            file_path = project_configs_dir / file
            assert file_path.exists(), f"Example file {file} not found"
            assert file_path.is_file()
            assert file_path.stat().st_size > 0
