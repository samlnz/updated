#!/usr/bin/env python3
"""
Simple runner for Bingo Bot
Use: python run.py [flask|bot|admin|all]
"""

import sys
import subprocess
import time
import os

def run_flask():
    """Run Flask web app"""
    print("🚀 Starting Flask web app...")
    os.system("python app.py")

def run_bot():
    """Run Telegram bot"""
    print("🤖 Starting Telegram bot...")
    os.system("python bot.py")

def run_admin():
    """Run admin panel"""
    print("👑 Starting admin panel...")
    os.system("python admin_panel.py")

def run_all():
    """Run all services in separate processes"""
    print("🎰 Starting all Bingo Bot services...")
    
    # Import multiprocessing
    from multiprocessing import Process
    
    processes = []
    
    # Start Flask
    flask_proc = Process(target=run_flask)
    processes.append(flask_proc)
    
    # Start Admin Panel
    admin_proc = Process(target=run_admin)
    processes.append(admin_proc)
    
    # Start processes
    for proc in processes:
        proc.start()
        time.sleep(1)
    
    print("\n" + "="*50)
    print("✅ Services started:")
    print(f"🌐 Web App: http://localhost:5000")
    print(f"👑 Admin: http://localhost:5001/admin/login")
    print("🤖 Bot: Running...")
    print("="*50)
    print("\nPress Ctrl+C to stop all services\n")
    
    # Run bot in main process
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        for proc in processes:
            proc.terminate()
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "flask":
            run_flask()
        elif command == "bot":
            run_bot()
        elif command == "admin":
            run_admin()
        elif command == "all":
            run_all()
        else:
            print("Usage: python run.py [flask|bot|admin|all]")
    else:
        # Default: run all
        run_all()