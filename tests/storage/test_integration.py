"""
Simple integration test for storage functionality.
This test can be run independently to verify storage components work correctly.
"""

import io
import tempfile
import os
from unittest.mock import Mock, patch

def test_storage_components_import():
    """Test that all storage components can be imported correctly."""
    try:
        from src.storage import (
            MinIOClient,
            get_minio_client,
            ArtifactStorage,
            MetadataManager,
            AccessControl,
            StorageUtils,
            get_artifact_storage_service,
            get_metadata_manager_service,
            get_access_control_service,
            get_storage_utils
        )
        print("✅ All storage components imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_storage_utils_functionality():
    """Test storage utilities functionality."""
    try:
        from src.storage.utils import StorageUtils
        
        utils = StorageUtils()
        
        # Test filename sanitization
        sanitized = utils.sanitize_filename("test<file>.txt")
        assert sanitized == "test_file_.txt"
        
        # Test file extension validation
        assert utils.validate_file_extension("test.txt") == True
        assert utils.validate_file_extension("test.exe") == False
        
        # Test file size validation
        assert utils.validate_file_size(1024) == True
        assert utils.validate_file_size(200 * 1024 * 1024) == False  # 200MB
        
        print("✅ Storage utilities functionality test passed")
        return True
    except Exception as e:
        print(f"❌ Storage utilities test failed: {e}")
        return False

def test_artifact_storage_creation():
    """Test artifact storage service creation."""
    try:
        from src.storage.artifact_storage import ArtifactStorage
        from unittest.mock import Mock
        
        mock_client = Mock()
        storage = ArtifactStorage(mock_client)
        
        assert storage is not None
        assert hasattr(storage, 'upload_artifact')
        assert hasattr(storage, 'download_artifact')
        assert hasattr(storage, 'get_artifact_metadata')
        
        print("✅ Artifact storage service creation test passed")
        return True
    except Exception as e:
        print(f"❌ Artifact storage test failed: {e}")
        return False

def test_access_control_creation():
    """Test access control service creation."""
    try:
        from src.storage.access_control import AccessControl
        from unittest.mock import Mock
        
        mock_client = Mock()
        access_control = AccessControl(mock_client)
        
        assert access_control is not None
        assert hasattr(access_control, 'set_artifact_visibility')
        assert hasattr(access_control, 'check_access_permission')
        assert hasattr(access_control, 'generate_presigned_url')
        
        print("✅ Access control service creation test passed")
        return True
    except Exception as e:
        print(f"❌ Access control test failed: {e}")
        return False

def test_metadata_manager_creation():
    """Test metadata manager service creation."""
    try:
        from src.storage.metadata_manager import MetadataManager
        from unittest.mock import Mock
        
        mock_client = Mock()
        metadata_manager = MetadataManager(mock_client)
        
        assert metadata_manager is not None
        assert hasattr(metadata_manager, 'add_metadata_tags')
        assert hasattr(metadata_manager, 'search_artifacts_by_metadata')
        
        print("✅ Metadata manager service creation test passed")
        return True
    except Exception as e:
        print(f"❌ Metadata manager test failed: {e}")
        return False

def run_all_tests():
    """Run all storage integration tests."""
    print("🧪 Running Storage Integration Tests...")
    print("=" * 50)
    
    tests = [
        test_storage_components_import,
        test_storage_utils_functionality,
        test_artifact_storage_creation,
        test_access_control_creation,
        test_metadata_manager_creation,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All storage integration tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    run_all_tests()
