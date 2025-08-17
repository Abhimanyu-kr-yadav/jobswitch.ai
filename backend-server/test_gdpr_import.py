"""Test GDPR import"""
import sys
import os
sys.path.append('.')

# Test individual imports first
print("Testing individual imports...")

try:
    from app.core.data_anonymization import data_anonymizer, pii_detector
    print("✓ data_anonymization imports OK")
except Exception as e:
    print(f"✗ data_anonymization import failed: {e}")

try:
    from app.core.security import encryption
    print("✓ security encryption import OK")
except Exception as e:
    print(f"✗ security encryption import failed: {e}")

# Now test the full module
try:
    print("\nAttempting to import GDPR module...")
    
    # Read and execute the file directly to see where it fails
    with open('app/core/gdpr_compliance.py', 'r') as f:
        content = f.read()
    
    # Create a namespace to execute in
    namespace = {}
    exec(content, namespace)
    
    print(f"Namespace keys: {list(namespace.keys())}")
    
    if 'GDPRComplianceManager' in namespace:
        print("✓ GDPRComplianceManager found in namespace")
    else:
        print("✗ GDPRComplianceManager not found in namespace")
        
except Exception as e:
    print(f"Execution failed: {e}")
    import traceback
    traceback.print_exc()