import os
from pathlib import Path

from rich import print
from rich.markdown import Markdown

from storage import Resource, RuntimeData


class Chores:
    """
    A class to handle pre-execution and post-execution chores like generating reports and cleaning up temporary files.
    """
    def __init__(self, workdir: str, dump_output: bool, generate_report: bool, storage: RuntimeData):
        """
        Initializes the Chores object.

        Args:
            workdir: The working directory for the chores.
            dump_output: Whether to dump the command outputs to a file.
            generate_report: Whether to generate a report file.
            storage: The RuntimeData object containing the storage information.
        """
        self.workdir = workdir
        self.should_dump_output = dump_output
        self.should_generate_report = generate_report
        self.storage = storage
        Path(self.workdir).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def indexed_filename(filename: str) -> str:
        """
        Generates an indexed filename if the original filename already exists.

        Args:
            filename: The original filename.

        Returns:
            The indexed filename.
        """
        i = 0
        name = filename.split('.')[0]
        extension = filename.split('.')[1]
        while os.path.exists(f'{name} ({i}).{extension}'):
            i += 1

        return f'{name} ({i}).{extension}'

    @classmethod
    def get_valid_filename(cls, filename: str) -> str:
        """
        Checks if a filename already exists and prompts the user for action.

        Args:
            filename: The filename to check.

        Returns:
            The valid filename, either the original or an indexed version.
        """
        if os.path.isfile(filename):
            choice = input(f'File "{filename}" already exists. Do you want to overwrite? (y/n):')
            if choice.lower() in ['y', 'yes', 'true', '1', 't', 'sure', 'ok', 'okay']:
                return filename
            else:
                return cls.indexed_filename(filename)
        return filename

    def dump_output(self, filename: str = 'outputs.md'):
        """
        Dumps the command outputs to a Markdown file.

        Args:
            filename: The name of the output file.
        """
        filename = self.get_valid_filename(filename)
        with open(filename, 'w') as f:
            f.write('## Outputs\n')
            for output in self.storage.outputs:
                f.write(output.get_markdown())

        self.storage.resources.append(
            Resource(
                name='Output dump',
                path=filename,
                details='A dump of all the executed commands',
                type='Markdown file'
            )
        )

    def get_notes(self):
        """
        Generates a Markdown string containing all the notes.

        Returns:
            A Markdown string containing all the notes.
        """
        notes = '# Notes\n'
        for message in self.storage.notes:
            notes += message.get_markdown()
        return notes

    def get_resources_markdown(self):
        """
        Generates a Markdown string containing a table of resources.

        Returns:
            A Markdown string containing a table of resources.
        """
        resources_md = '# Resources\n'
        resources_md += Resource.get_table_header()

        for resource in self.storage.resources:
            resources_md += resource.get_row_markdown()
        return resources_md

    def generate_report(self, filename: str = 'report.md'):
        """
        Generates a report file containing notes and resources.

        Args:
            filename: The name of the report file.
        """
        if self.storage.resources or self.storage.notes:
            filename = self.get_valid_filename(filename)
            self.storage.resources.append(
                Resource(
                    name='Cluster Report',
                    path=filename,
                    details='A report containing all the details about the created cluster',
                    type='Markdown file'
                )
            )
            report = ''
            if self.storage.notes:
                report = self.get_notes()

            if self.storage.resources:
                report += '\n' + self.get_resources_markdown()

            print(Markdown(report))

            with open(filename, 'w') as file:
                file.write(report)

    def delete_temporary_files(self):
        """
        Deletes all temporary files created during the process.
        """
        for file in self.storage.temp_files:
            os.remove(file)

    def cleanup(self):
        """
        Performs cleanup tasks based on the configuration.
        """
        if self.should_dump_output and self.storage.outputs:
            self.dump_output('outputs.md')
        if self.should_generate_report:
            self.generate_report('report.md')
        self.delete_temporary_files()
