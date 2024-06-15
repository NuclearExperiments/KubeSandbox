import json
import logging.config
import os
import sys
from pathlib import Path

from kubesandbox.chores import Chores
from kubesandbox.storage import RuntimeData

banner = r"""
▉▉\   ▉▉\          ▉▉\                  ▉▉▉▉▉▉\                            ▉▉\ ▉▉\                           
▉▉ | ▉▉  |         ▉▉ |                ▉▉  __▉▉\                           ▉▉ |▉▉ |                          
▉▉ |▉▉  /▉▉\   ▉▉\ ▉▉▉▉▉▉▉\   ▉▉▉▉▉▉\  ▉▉ /  \__| ▉▉▉▉▉▉\  ▉▉▉▉▉▉▉\   ▉▉▉▉▉▉▉ |▉▉▉▉▉▉▉\   ▉▉▉▉▉▉\  ▉▉\   ▉▉\ 
▉▉▉▉▉  / ▉▉ |  ▉▉ |▉▉  __▉▉\ ▉▉  __▉▉\ \▉▉▉▉▉▉\   \____▉▉\ ▉▉  __▉▉\ ▉▉  __▉▉ |▉▉  __▉▉\ ▉▉  __▉▉\ \▉▉\ ▉▉  |
▉▉  ▉▉<  ▉▉ |  ▉▉ |▉▉ |  ▉▉ |▉▉▉▉▉▉▉▉ | \____▉▉\  ▉▉▉▉▉▉▉ |▉▉ |  ▉▉ |▉▉ /  ▉▉ |▉▉ |  ▉▉ |▉▉ /  ▉▉ | \▉▉▉▉  / 
▉▉ |\▉▉\ ▉▉ |  ▉▉ |▉▉ |  ▉▉ |▉▉   ____|▉▉\   ▉▉ |▉▉  __▉▉ |▉▉ |  ▉▉ |▉▉ |  ▉▉ |▉▉ |  ▉▉ |▉▉ |  ▉▉ | ▉▉  ▉▉<  
▉▉ | \▉▉\\▉▉▉▉▉▉  |▉▉▉▉▉▉▉  |\▉▉▉▉▉▉▉\ \▉▉▉▉▉▉  |\▉▉▉▉▉▉▉ |▉▉ |  ▉▉ |\▉▉▉▉▉▉▉ |▉▉▉▉▉▉▉  |\▉▉▉▉▉▉  |▉▉  /\▉▉\ 
\__|  \__|\______/ \_______/  \_______| \______/  \_______|\__|  \__| \_______|\_______/  \______/ \__/  \__|
"""

intro = f'''
{banner}

'''
home_dir = str(Path.home())
workdir = os.environ.get('WORKDIR', os.path.join(home_dir, '.kubesandbox'))
node_port_base = os.environ.get('NODE_PORT_BASE', '3200')
generate_report = (os.environ.get('GENERATE_REPORT', 'true').lower() in ['true', '1', 'yes', 'y', 't'])
dump_output = (os.environ.get('DUMP_OUTPUT', 'false').lower() in ['true', '1', 'yes', 'y', 't'])
run_in_user_namespace = (os.environ.get('RUN_IN_USER_NAMESPACE', 'true').lower() in ['true', '1', 'yes', 'y', 't'])

storage = RuntimeData()
chores = Chores(workdir=workdir, storage=storage, dump_output=dump_output, generate_report=generate_report)
# chores.perform_startup_tasks()

logging_config = os.environ.get('LOGGING_CONFIG', '''
{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "simple": {
            "format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
        }
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },
        "stderr": {
            "class": "logging.StreamHandler",
            "level": "ERROR",
            "formatter": "simple",
            "stream": "ext://sys.stderr"
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "simple",
            "filename": ''' + f'"{os.path.join(workdir, "kubesandbox.log")}",' + '''
            "mode": "w"
        },
        "shellexec": {
            "class": "logging.FileHandler",
            "formatter": "simple",
            "filename": ''' + f'"{os.path.join(workdir, "shellexec.log")}",' + '''
            "mode": "w"
        }
    },
    "loggers": {
        "Shell": {
            "level": "DEBUG",
            "handlers": [
                "shellexec"
            ]
        },
        "App": {
            "level": "DEBUG",
            "handlers": [
                "stderr",
                "stdout",
                "file"
            ]
        }
    }
}''')

logging.config.dictConfig(json.loads(logging_config))


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = Path(__file__).parent.absolute()

    return os.path.join(base_path, relative_path)


installer_config = os.environ.get('INSTALLER_CONFIG', '''
{
    "docker": {
        "url": "https://get.docker.com",
        "requires_root": true
    },
    "k3d": {
        "url": "https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh",
        "requires_root": false
    },
    "kubectl": {
        "url": "https://raw.githubusercontent.com/Prakhar225/placeholder/main/kubectl.sh",
        "requires_root": true
    },
    "helm": {
        "url": "https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3",
        "requires_root": false
    }

}
''')

with open(resource_path('../deployment_config.json'), 'r') as f:
    deployment_config = json.load(f)
