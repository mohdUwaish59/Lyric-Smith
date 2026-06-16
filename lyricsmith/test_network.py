#!/usr/bin/env python3
"""
Test network connectivity for HuggingFace API
"""

import urllib.request
import socket

def test_dns():
    """Test DNS resolution."""
    print("1. Testing DNS resolution...")
    try:
        socket.gethostbyname('google.com')
        print("   ✅ DNS works - google.com resolved")
        return True
    except socket.gaierror:
        print("   ❌ DNS failed - cannot resolve hostnames")
        print("   → Try: ipconfig /flushdns")
        return False

def test_internet():
    """Test basic internet connectivity."""
    print("\n2. Testing internet connectivity...")
    try:
        urllib.request.urlopen('https://www.google.com', timeout=5)
        print("   ✅ Internet works - Google reachable")
        return True
    except Exception as e:
        print(f"   ❌ No internet: {e}")
        print("   → Check your connection")
        return False

def test_huggingface():
    """Test HuggingFace API accessibility."""
    print("\n3. Testing HuggingFace API...")
    try:
        urllib.request.urlopen('https://huggingface.co', timeout=10)
        print("   ✅ HuggingFace reachable")
        return True
    except Exception as e:
        print(f"   ❌ Cannot reach HuggingFace: {e}")
        print("   → Firewall/proxy might be blocking")
        return False

def main():
    print("="*70)
    print("Network Connectivity Test for LyricSmith")
    print("="*70)
    print()
    
    dns_ok = test_dns()
    internet_ok = test_internet()
    hf_ok = test_huggingface()
    
    print("\n" + "="*70)
    print("Summary")
    print("="*70)
    
    if dns_ok and internet_ok and hf_ok:
        print("\n✅ ALL TESTS PASSED")
        print("   → You can use HuggingFace API")
        print("   → Run: python chat.py → Backend: 2")
    else:
        print("\n❌ NETWORK ISSUES DETECTED")
        print("\n📝 Recommendation: Use LOCAL OLLAMA instead")
        print("\n   Option 1 - Current model (works now):")
        print("      ollama serve")
        print("      python chat.py → Backend: 1 → Model: llama3.1")
        print("      Quality: 3/10, Storage: 4.7 GB")
        
        print("\n   Option 2 - Better model (recommended):")
        print("      ollama pull qwen2.5:7b")
        print("      ollama serve")
        print("      python chat.py → Backend: 1 → Model: qwen2.5:7b")
        print("      Quality: 7/10, Storage: 4.7 GB (same size!)")
        
        print("\n   Option 3 - Best model (if you have RAM):")
        print("      ollama pull qwen2.5:14b")
        print("      ollama serve")
        print("      python chat.py → Backend: 1 → Model: qwen2.5:14b")
        print("      Quality: 8/10, Storage: 9 GB")
    
    print("\n" + "="*70)
    
    if not dns_ok:
        print("\n💡 DNS Issue Fix:")
        print("   Run: ipconfig /flushdns")
    
    if not internet_ok:
        print("\n💡 Internet Issue Fix:")
        print("   - Check WiFi/Ethernet connection")
        print("   - Try mobile hotspot")
        print("   - Disable VPN temporarily")
    
    if not hf_ok and internet_ok:
        print("\n💡 HuggingFace Blocked Fix:")
        print("   - Check Windows Firewall")
        print("   - Disable proxy/VPN")
        print("   - Use local Ollama instead")

if __name__ == "__main__":
    main()
