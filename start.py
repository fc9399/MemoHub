#!/usr/bin/env python3
"""
UniMem AI Startup Script
"""
import os
import sys
import subprocess
from pathlib import Path

def check_environment():
    """Check environment configuration"""
    print("🔍 Checking environment configuration...")
    
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found, please create and configure environment variables")
        print("📝 Required variables:")
        print("   - AWS_ACCESS_KEY_ID")
        print("   - AWS_SECRET_ACCESS_KEY")
        print("   - AWS_REGION")
        print("   - S3_BUCKET_NAME")
        print("   - NVIDIA_API_KEY")
        print("   - ENVIRONMENT (development/production)")
        return False
    
    print("✅ .env file exists")
    return True

def install_dependencies():
    """Install dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def start_server():
    """Start server"""
    print("🚀 Starting UniMem AI server...")
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start server: {e}")

def main():
    """Main function"""
    print("🧠 UniMem AI - Personal Memory Hub")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        return
    
    # Install dependencies
    if not install_dependencies():
        return
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()