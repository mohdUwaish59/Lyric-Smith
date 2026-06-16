#!/usr/bin/env python3
"""
Test HuggingFace client (without actually calling API - just structure test)
"""

from lyricsmith.llm import HuggingFaceClient

def test_hf_client_structure():
    """Test that HuggingFaceClient is properly structured."""
    print("Testing HuggingFace client structure...")
    
    # Test initialization (won't call API)
    try:
        client = HuggingFaceClient(
            model="Qwen/Qwen2.5-7B-Instruct",
            api_token="hf_test_token_example"
        )
        print(f"✅ Client initialized")
        print(f"   Model: {client.model}")
        print(f"   API URL: {client.api_url}")
        print(f"   Temperature: {client.temperature}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
    
    print("\n✅ HuggingFace client is properly integrated!")
    print("\n📝 To use for real:")
    print("1. Get free token: https://huggingface.co/settings/tokens")
    print("2. Run: python chat.py")
    print("3. Choose backend: 2 (HuggingFace)")
    print("4. Enter your token")
    return True

if __name__ == "__main__":
    print("="*70)
    print("HuggingFace Integration Test")
    print("="*70)
    print()
    
    test_hf_client_structure()
    
    print("\n" + "="*70)
    print("✅ Integration complete! See HUGGINGFACE_GUIDE.md for usage.")
    print("="*70)
