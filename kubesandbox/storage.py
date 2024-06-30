from typing import Optional

from pydantic import BaseModel, Field


class Resource(BaseModel):
    name: str
    path: str
    type: str
    details: Optional[str] = '-'
    reference: Optional[str] = '-'

    @staticmethod
    def get_table_header():
        header = '| Name | Type | Path | Details | References |\n'
        header += '| --- | --- | --- | --- | --- |\n'
        return header

    def get_row_markdown(self):
        return f'| {self.name} | {self.type} | {self.path} | {self.details} | {self.reference} |\n'


class CommandOutput(BaseModel):
    title: str
    stdout: str
    stderr: str
    exit_code: int

    def get_markdown(self):
        return f'''
## {self.title}
### Stdout
```
{self.stdout}
```
### Stderr
```
{self.stderr}
```
'''


class ReportNote(BaseModel):
    title: Optional[str] = None
    message: str

    def get_markdown(self):
        if self.title:
            return f'## {self.title} \n{self.message}\n\n'
        else:
            return f'{self.message}\n\n'


class InputParameters(BaseModel):
    cluster_name: str = 'sandbox'
    agents: int = 0
    servers: int = 1
    registry: bool = True
    loadbalancer: Optional[tuple[int, int]] = (80, 443)
    nodeports: int = 0
    ingress: Optional[str] = 'nginx'
    management_tool: Optional[str] = None


class RuntimeData(BaseModel):
    inputs: InputParameters = InputParameters()
    outputs: list[CommandOutput] = []
    resources: list[Resource] = Field(default_factory=list, description='Generated output files')
    notes: list[ReportNote] = Field(default_factory=list,
                                    description='Messages to be printed at the end of the process')
    temp_files: list[str] = Field(default_factory=list, description='Files to be deleted at the end of the process')
