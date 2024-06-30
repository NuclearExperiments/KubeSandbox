import questionary
from questionary import Separator, Choice, Style

from kubesandbox import config

custom_style_fancy = Style([
    ('qmark', 'fg:#673ab7'),  # token in front of the question
    ('question', 'bold italic underline fg:#3d69ad  '),  # question text
    ('answer', 'fg:#f44336 bold'),  # submitted answer text behind the question
    ('pointer', 'fg:#21aa08  bold'),  # pointer used in select and checkbox prompts
    ('highlighted', 'fg:#21aa08  bold'),  # pointed-at choice in select and checkbox prompts
    ('selected', 'fg:#cc5454'),  # style for a selected item of a checkbox
    # ('separator', 'fg:#cc5454'),  # separator in lists
    ('instruction', ''),  # user instructions for select, rawselect, checkbox
    ('text', ''),  # plain text
    ('disabled', 'fg:#858585 italic')  # disabled choices for select and checkbox prompts
])


class InputMenus:
    basic_build_menu: list[dict] = [
        {
            "type": "print",
            "message": config.intro,
        },
        {
            "type": "text",
            "name": "agents",
            "message": "How many worker nodes do you need? (Consumes additional resources. Set to 0 if not required.)",
            "default": '0',
            "validate": lambda answer: True if answer.isnumeric() and int(
                answer) <= 3 else "Please enter a number between 0 and 3"
        },
        {
            "type": "confirm",
            "name": "registry",
            "message": "Do you want to use a local registry? [Useful if want to reuse the pulled images.]",
            "default": True
        },
        {
            "type": "select",
            "name": "loadbalancer",
            "message": "Select a load balancer mapping. [One of the ways to access the cluster. Required for "
                       "ingresses.]",
            "choices": [
                "Direct mapping (maps port 80:80 and 443:443 to allow URLs like 'http://rancher.localhost' but "
                "requires root access)",
                "Indirect mapping (maps port 80 to 8080 and 443 to 4433)",
                Separator(),
                "No load balancer mapping"
            ],
            "default": "Direct mapping (maps port 80:80 and 443:443 to allow URLs like 'http://rancher.localhost' but "
                       "requires root access)"
        },
        {
            "type": "text",
            "name": "nodeports",
            "message": "How many node ports do you need? [Alternative to the load balancer, "
                       "not usually required but you can have both]",
            "validate": lambda answer: True if answer.isnumeric() and int(
                answer) <= 6 else "Please enter a number between 0 and 6",
            "default": "0"
        },
        {
            "type": "select",
            "name": "ingress",
            "message": "Select an ingress controller:",
            "choices": ["Nginx", "Traefik", "APISIX", "Kong", Separator(), "No ingress controller"],
            "default": "Nginx"
        },
        {
            "type": "select",
            "name": "management",
            "message": "Select an cluster management tool [These are powerful tools but not recommended "
                       "if your system specifications are low]:",
            "choices": ["Rancher", "Kubesphere", Separator(), "None"],
            "default": "None"
        },

    ]
    main_menu: list = [
        # Separator(),
        Separator(),
        Choice(title='Easy mode (No management tool) - Build cluster with default configurations', value='build_light'),
        Choice(title='Easy mode (Rancher) - Build cluster with default configurations and Rancher for management',
               value='build_heavy'),
        Choice(title='Basic mode - Build cluster and provide basic configurations', value='basic'),
        Choice(title='Build cluster using configuration file', value='recreate',
               disabled='Planned for future release'),
        Choice(title='Advanced mode - Build a highly customized cluster', value='advanced',
               disabled='Planned for future release'),
        Separator(),
        Choice(title='Delete sandbox cluster', value='delete'),
        Choice(title='Patch permissions for rootless docker', value='patch_docker'),
        Separator(),
        Choice(title='Exit', value='exit'),
    ]
    main_menu_meta: dict[str, str] = {
        'Build cluster using configuration file': 'Mike testing hello'
    }

    @classmethod
    def get_build_description(cls) -> None:
        description = questionary.prompt(cls.basic_build_menu)
        cls.parse_description(description)

    @classmethod
    def get_main_menu(cls) -> str:
        return questionary.select(message=f'{config.intro}Select an option to continue:', choices=cls.main_menu,
                                  qmark=' ',
                                  style=custom_style_fancy).ask()

    @classmethod
    def parse_description(cls, description):
        inputs = config.storage.inputs

        inputs.agents = int(description['agents'])
        inputs.nodeports = int(description['nodeports'])
        inputs.registry = description['registry']

        inputs.ingress = description['ingress'].lower() if description['ingress'] != 'No ingress controller' else None

        if f"{description['loadbalancer']}".startswith('Direct'):
            inputs.loadbalancer = (80, 443)
        elif f"{description['loadbalancer']}".startswith('Indirect'):
            inputs.loadbalancer = (8080, 4433)
        else:
            inputs.loadbalancer = None

        inputs.management_tool = description['management'].lower()

