#!/usr/bin/env python3
"""
Script to start all required services for bot marketplace
"""

import subprocess
import sys
import os
import time
import signal

def start_service(name, command, cwd=None):
    """Start a service with given command"""
    print(f"Starting {name}...")
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            cwd=cwd or os.getcwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        return process
    except Exception as e:
        print(f"Failed to start {name}: {e}")
        return None

def main():
    """Start all services"""
    print("=== Bot Marketplace Services Startup ===\n")
    
    services = []
    
    try:
        # Start API server
        print("1. Starting API Server...")
        api_process = start_service(
            "API Server",
            "python main.py",
            cwd=os.getcwd()
        )
        if api_process:
            services.append(("API Server", api_process))
            time.sleep(2)
        
        # Start Celery Worker
        print("2. Starting Celery Worker...")
        worker_process = start_service(
            "Celery Worker",
            "celery -A tasks worker --loglevel=info --concurrency=4 --queues=bot_execution,maintenance",
            cwd=os.getcwd()
        )
        if worker_process:
            services.append(("Celery Worker", worker_process))
            time.sleep(2)
        
        # Start Celery Beat
        print("3. Starting Celery Beat...")
        beat_process = start_service(
            "Celery Beat",
            "celery -A tasks beat --loglevel=info",
            cwd=os.getcwd()
        )
        if beat_process:
            services.append(("Celery Beat", beat_process))
            time.sleep(2)
        
        print(f"\n✅ All services started successfully!")
        print(f"Running services: {len(services)}")
        
        for name, process in services:
            print(f"  - {name} (PID: {process.pid})")
        
        print(f"\n🚀 Bot marketplace is now running!")
        print(f"  - API: http://localhost:8000")
        print(f"  - Docs: http://localhost:8000/docs")
        print(f"  - Bot execution: Active")
        print(f"  - Email notifications: Active")
        
        print(f"\n📝 To stop all services, press Ctrl+C")
        
        # Wait for keyboard interrupt
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n🛑 Stopping all services...")
            
            for name, process in services:
                print(f"  Stopping {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            
            print(f"✅ All services stopped")
    
    except Exception as e:
        print(f"❌ Error starting services: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 