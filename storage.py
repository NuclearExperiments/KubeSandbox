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


class RuntimeData(BaseModel):
    inputs: dict[str, str] = {}
    outputs: list[CommandOutput] = []
    resources: list[Resource] = Field(default_factory=list, description='Generated output files')
    notes: list[ReportNote] = Field(default_factory=list,
                                    description='Messages to be printed at the end of the process')
    temp_files: list[str] = Field(default_factory=list, description='Files to be deleted at the end of the process')
