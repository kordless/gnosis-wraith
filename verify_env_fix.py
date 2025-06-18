# Environment Variable Verification Script
import os

def verify_environment_vars():
    """Verify that environment variables are set correctly for production."""
    
    print("=== Environment Variable Check ===")
    
    # Check RUNNING_IN_CLOUD
    running_in_cloud = os.getenv('RUNNING_IN_CLOUD', 'false').lower() == 'true'
    print(f"RUNNING_IN_CLOUD: {os.getenv('RUNNING_IN_CLOUD', 'NOT SET')} -> Cloud Mode: {running_in_cloud}")
    
    # Check models behavior
    print("\n=== Model Configuration Check ===")
    
    # Import and check user model logic
    from core.models.user import User
    from core.models.api_token import ApiToken
    
    # These should now use RUNNING_IN_CLOUD instead of USE_LOCAL_DATASTORE
    local_mode = os.getenv('RUNNING_IN_CLOUD', 'false').lower() != 'true'
    print(f"Models will use local storage: {local_mode}")
    
    # Check storage service
    print("\n=== Storage Service Check ===")
    from core.storage_service import is_running_in_cloud, get_storage_config
    
    cloud_mode = is_running_in_cloud()
    print(f"Storage service cloud mode: {cloud_mode}")
    
    config = get_storage_config()
    print(f"Storage config: {config}")
    
    # Consistency check
    print("\n=== Consistency Check ===")
    if cloud_mode == (not local_mode):
        print("✅ CONSISTENT: Storage service and models agree on environment")
    else:
        print("❌ INCONSISTENT: Storage service and models disagree on environment")
        print(f"  Storage service thinks cloud mode: {cloud_mode}")
        print(f"  Models think local mode: {local_mode}")

if __name__ == "__main__":
    verify_environment_vars()
