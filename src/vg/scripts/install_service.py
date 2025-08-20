#!/usr/bin/env python3
"""
VG APIs System Service Installation Script
"""

import os
import sys
import subprocess
import shutil
import getpass
from pathlib import Path


def get_current_user():
    """Get the current user name"""
    return getpass.getuser()


def get_python_executable():
    """Get the current Python executable path"""
    return sys.executable


def get_project_root():
    """Get the project root directory"""
    return Path(__file__).parent.parent.parent.parent.absolute()


def create_systemd_service():
    """Create systemd service file content"""
    user = get_current_user()
    python_exec = get_python_executable()
    project_root = get_project_root()
    
    # Use uv if available, otherwise use pip
    uv_path = shutil.which('uv')
    if uv_path:
        exec_command = f"{uv_path} run vg_apis_service"
        working_dir = project_root
    else:
        exec_command = f"{python_exec} -m vg.main run_service"
        working_dir = project_root
    
    service_content = f"""[Unit]
Description=VG APIs FastAPI Service
After=network.target
Wants=network.target

[Service]
Type=exec
User={user}
Group={user}
WorkingDirectory={working_dir}
Environment=PATH=/usr/bin:/usr/local/bin:{os.environ.get('PATH', '')}
Environment=PYTHONPATH={project_root}/src
Environment=HOST=0.0.0.0
Environment=PORT=8000
ExecStart={exec_command}
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=vg-apis

[Install]
WantedBy=multi-user.target
"""
    return service_content


def install_service():
    """Install the systemd service"""
    if os.geteuid() == 0:
        print("❌ Please don't run this script as root!")
        print("💡 Run as your regular user - the script will use sudo when needed.")
        sys.exit(1)
    
    service_name = "vg-apis.service"
    service_content = create_systemd_service()
    
    # Create temporary service file
    temp_service_path = f"/tmp/{service_name}"
    
    try:
        # Write service file to temp location
        with open(temp_service_path, 'w') as f:
            f.write(service_content)
        
        print(f"📝 Created service file: {temp_service_path}")
        
        # Copy to systemd directory (requires sudo)
        print("🔐 Installing service (requires sudo)...")
        subprocess.run([
            "sudo", "cp", temp_service_path, f"/etc/systemd/system/{service_name}"
        ], check=True)
        
        # Set proper permissions
        subprocess.run([
            "sudo", "chmod", "644", f"/etc/systemd/system/{service_name}"
        ], check=True)
        
        # Reload systemd
        print("🔄 Reloading systemd...")
        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
        
        # Enable service
        print("✅ Enabling service...")
        subprocess.run(["sudo", "systemctl", "enable", service_name], check=True)
        
        print(f"🎉 Service '{service_name}' installed successfully!")
        print()
        print("📋 Service management commands:")
        print(f"   Start:   sudo systemctl start {service_name}")
        print(f"   Stop:    sudo systemctl stop {service_name}")
        print(f"   Status:  sudo systemctl status {service_name}")
        print(f"   Logs:    sudo journalctl -u {service_name} -f")
        print(f"   Restart: sudo systemctl restart {service_name}")
        print()
        
        # Ask if user wants to start the service now
        response = input("🚀 Start the service now? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            subprocess.run(["sudo", "systemctl", "start", service_name], check=True)
            print("✅ Service started!")
            
            # Show status
            subprocess.run(["sudo", "systemctl", "status", service_name, "--no-pager"])
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing service: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        # Clean up temp file
        if os.path.exists(temp_service_path):
            os.remove(temp_service_path)


def uninstall_service():
    """Uninstall the systemd service"""
    service_name = "vg-apis.service"
    
    try:
        # Stop service if running
        print("🛑 Stopping service...")
        subprocess.run(["sudo", "systemctl", "stop", service_name], 
                      capture_output=True)
        
        # Disable service
        print("❌ Disabling service...")
        subprocess.run(["sudo", "systemctl", "disable", service_name], 
                      capture_output=True)
        
        # Remove service file
        service_path = f"/etc/systemd/system/{service_name}"
        if os.path.exists(service_path):
            print("🗑️  Removing service file...")
            subprocess.run(["sudo", "rm", service_path], check=True)
        
        # Reload systemd
        print("🔄 Reloading systemd...")
        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
        
        print(f"✅ Service '{service_name}' uninstalled successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error uninstalling service: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


def show_help():
    """Show help information"""
    print("VG APIs System Service Management")
    print("=================================")
    print()
    print("Commands:")
    print("  install     Install the service")
    print("  uninstall   Uninstall the service")
    print("  help        Show this help")
    print()
    print("Examples:")
    print("  uv run install_service")
    print("  uv run uninstall_service")


def main():
    """Main function for service installation"""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        show_help()
        return
    
    print("🔧 VG APIs System Service Installer")
    print("===================================")
    print()
    
    # Check if systemd is available
    if not shutil.which('systemctl'):
        print("❌ systemctl not found. This script requires systemd.")
        sys.exit(1)
    
    install_service()


def uninstall():
    """Main function for service uninstallation"""
    print("🗑️  VG APIs System Service Uninstaller")
    print("======================================")
    print()
    
    # Check if systemd is available
    if not shutil.which('systemctl'):
        print("❌ systemctl not found. This script requires systemd.")
        sys.exit(1)
    
    uninstall_service()


if __name__ == "__main__":
    main()
