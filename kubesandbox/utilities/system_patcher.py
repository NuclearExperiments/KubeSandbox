import os
import subprocess
import sys
import traceback


class Patcher:
    @staticmethod
    def check_root_status():
        if os.name == 'nt':
            import ctypes
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except:
                traceback.print_exc()
                return False
        elif os.name == 'posix':
            return os.getuid() == 0
        else:
            raise RuntimeError(f'Unsupported operating system for this module: {os.name}')

    @staticmethod
    def execute(command: str, on_complete='done\n'):
        process = subprocess.Popen(f'{command} && echo {on_complete}', shell=True, stdin=subprocess.PIPE, text=True)
        process.communicate()

    @staticmethod
    def patch_docker_cgroup_permissions():
        print('Patching docker cgroup permissions\n')

        print('Creating systemd directory')
        Patcher.execute('sudo mkdir -p /etc/systemd/system/user@.service.d')

        print('Creating delegate.conf')
        Patcher.execute('''sudo bash -c "cat > /etc/systemd/system/user@.service.d/delegate.conf << EOF
[Service]
Delegate=cpu cpuset io memory pids 
EOF"''')

        print('Reloading systemd')
        Patcher.execute('sudo systemctl daemon-reload')

    @staticmethod
    def patch_docker_port_permissions():
        print('Patching docker port permissions')

        print('Setting port capabilities for docker')
        Patcher.execute('sudo setcap cap_net_bind_service=ep $(which rootlesskit)')

        print('Restarting docker')
        Patcher.execute('systemctl --user restart docker')
        Patcher.execute('sudo systemctl restart docker')

    @staticmethod
    def fix_rootless_docker():
        try:
            if Patcher.check_root_status():
                print('Please start the process without sudo. You will be asked to authenticate where required.\n')
                sys.exit(0)
            else:
                print('This process requires admin access. Please authenticate where required.\n\n')
                Patcher.execute('sudo echo ""', '')
                Patcher.patch_docker_port_permissions()
                Patcher.patch_docker_cgroup_permissions()
        except:
            print('''
Process failed. Please try again or fix manually as descried on the following links:
    
    https://docs.docker.com/engine/security/rootless/#limiting-resources
    https://docs.docker.com/engine/security/rootless/#exposing-privileged-ports
''')


if __name__ == '__main__':
    Patcher.fix_rootless_docker()
