import unittest
from unittest.mock import patch, MagicMock, call

from exception_classes import InstallationFailedException, UnknownPackageException
from planner.planner import ExecutionPlanner, InstallationSource
from planner.support import Step, DisplayMessages
from shellclient.base_shell import ProcessResult

example_url = 'https://example.com/package1.sh'

display_messages = DisplayMessages(
    ongoing_message='Dummy ongoing message',
    success_message='Dummy success message',
    failure_message='Dummy failure message'
)


def get_mock_display():
    mock_display = MagicMock()

    mock_display.add_item_to_logs.return_value = None
    mock_display.advance_progress_bar.return_value = None
    return mock_display


class TestExecutionPlanner(unittest.TestCase):

    def setUp(self):
        self.planner = ExecutionPlanner(steps=[])
        self.planner._display = get_mock_display()

    @patch('planner.planner.logger.info')
    @patch('planner.planner.logger.debug')
    @patch('planner.planner.httpx.get')
    def test_download_package_installation_script(self, mock_get, mock_debug, mock_info):
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = '#!/bin/bash\necho "Hello, world!"'
        mock_get.return_value.headers = {}
        self.planner.installation_sources = {
            'package1': InstallationSource(url=example_url)
        }
        script = self.planner._ExecutionPlanner__download_package_installation_script('package1')
        self.assertEqual(script, '#!/bin/bash\necho "Hello, world!"')
        mock_info.assert_called_once_with(
            'Downloading script for package "package1" from "https://example.com/package1.sh"'
        )
        mock_debug.assert_called_once_with(
            'Headers - {}\nStatus code - 200\nText - #!/bin/bash\necho "Hello, world!"'
        )

    @patch('planner.planner.logger.info')
    @patch('planner.planner.httpx.get')
    def test_download_package_installation_script_failure(self, mock_get, mock_info):
        mock_get.return_value.status_code = 404
        self.planner.installation_sources = {
            'package1': InstallationSource(url=example_url)
        }
        with self.assertRaises(InstallationFailedException):
            self.planner._ExecutionPlanner__download_package_installation_script('package1')
        mock_info.assert_called_once_with(
            'Downloading script for package "package1" from "https://example.com/package1.sh"'
        )

    # @patch('planner.planner.ExecutionPlanner._display')
    @patch('planner.planner.Shell.execute_command')
    @patch('planner.planner.logger.info')
    def test_execute_package_installation_script_success(self, mock_info, mock_execute_command):
        mock_execute_command.return_value = ProcessResult(exit_code=0, stdout='', stderr='')
        self.planner._ExecutionPlanner__execute_package_installation_script('package1', 'echo "Hello, world!"')
        mock_execute_command.assert_called_once_with(direct_command='bash -c \'echo "Hello, world!"\'')
        mock_info.assert_called_once_with('Package1 installed successfully')

    @patch('planner.planner.logger.info')
    @patch('planner.planner.Shell.execute_command')
    def test_execute_package_installation_script_failure(self, mock_execute_command, mock_info):
        mock_execute_command.return_value = ProcessResult(exit_code=1, stdout='', stderr='')
        with self.assertRaises(InstallationFailedException):
            self.planner._ExecutionPlanner__execute_package_installation_script('package1', 'echo "Hello, world!"')
        mock_execute_command.assert_called_once_with(direct_command='bash -c \'echo "Hello, world!"\'')
        mock_info.assert_called_once_with('Installation failed')

    # @patch('planner.planner.logger.info')
    # @patch.object(ExecutionPlanner, '__download_package_installation_script')
    # @patch.object(ExecutionPlanner, '__execute_package_installation_script')
    # # @patch('planner.planner.ExecutionPlanner.__download_package_installation_script')
    # # @patch('planner.planner.ExecutionPlanner.__execute_package_installation_script')
    # def test_install_package_success(self, mock_execute_package_installation_script,
    #                                  mock_download_package_installation_script, mock_info):
    #     mock_download_package_installation_script.return_value = 'echo "Hello, world!"'
    #
    #     self.planner.installation_sources = {
    #         'package1': InstallationSource(url=example_url)
    #     }
    #     self.planner._ExecutionPlanner__install_package('package1')
    #     mock_download_package_installation_script.assert_called_once_with('package1')
    #     mock_execute_package_installation_script.assert_called_once_with('package1', 'echo "Hello, world!"')
    #     mock_info.assert_has_calls([
    #         call('Installing package package1'),
    #         call('Downloading installation script for package package1', item_type='loading'),
    #         call('Installing package1', item_type='loading'),
    #         call('Package1 installed successfully', item_type='success')
    #     ])

    @patch('planner.planner.logger.info')
    def test_install_package_unknown_package(self, mock_info):
        with self.assertRaises(UnknownPackageException):
            self.planner._ExecutionPlanner__install_package('package1')

    @patch('planner.planner.httpx.get')
    @patch('planner.planner.Shell.execute_command')
    @patch('planner.planner.logger.info')
    def test_install_packages_success(self, mock_info, mock_execute_command, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = 'echo "Hello, world!"'
        mock_get.return_value.headers = {}

        mock_execute_command.return_value = ProcessResult(exit_code=0, stdout='', stderr='')

        self.planner.installation_sources = {
            'package1': InstallationSource(url=example_url),
            'package2': InstallationSource(url=f'{example_url}')
        }
        self.planner._ExecutionPlanner__install_packages({'package1', 'package2'})
        mock_execute_command.assert_has_calls([
            call(direct_command='sudo ls'),
            call(direct_command='bash -c \'echo "Hello, world!"\''),
            call(direct_command='bash -c \'echo "Hello, world!"\''),
        ], any_order=True)
        mock_info.assert_has_calls(
            [call('Installing package package2'),
             call(
                 'Downloading script for package "package2" from "https://example.com/package1.sh"'),
             call('Package2 installed successfully'),
             call('Installing package package1'),
             call(
                 'Downloading script for package "package1" from "https://example.com/package1.sh"'),
             call('Package1 installed successfully')],
            any_order=True
        )

    @patch('planner.planner.httpx.get')
    @patch('planner.planner.Shell.execute_command')
    @patch('planner.planner.logger.info')
    def test_install_packages_failure(self, mock_info, mock_execute_command, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = 'echo "Hello, world!"'
        mock_get.return_value.headers = {}

        mock_execute_command.side_effect = [
            ProcessResult(exit_code=0, stdout='', stderr=''),
            ProcessResult(exit_code=1, stdout='', stderr='')
        ]
        self.planner.installation_sources = {
            'package1': InstallationSource(url=example_url),
        }
        with self.assertRaises(InstallationFailedException):
            self.planner._ExecutionPlanner__install_packages({'package1'})
        mock_execute_command.assert_has_calls([
            call(direct_command='sudo ls'),
            call(direct_command='bash -c \'echo "Hello, world!"\'')
        ])
        mock_info.assert_has_calls([
            call('Installing package package1'),
            call('Downloading script for package "package1" from "https://example.com/package1.sh"'),
            call('Installation failed')
        ])

    @patch('planner.planner.Shell.execute_command')
    @patch('planner.planner.logger.info')
    def test_install_packages_keyboard_interrupt(self, mock_info, mock_execute_command):
        mock_execute_command.side_effect = [
            ProcessResult(exit_code=0, stdout='', stderr=''),
            KeyboardInterrupt
        ]
        self.planner.installation_sources = {
            'package1': InstallationSource(url=example_url),
        }
        with self.assertRaises(InstallationFailedException):
            self.planner._ExecutionPlanner__install_packages({'package1'})
        mock_execute_command.assert_has_calls([
            call(direct_command='sudo ls')
        ])
        mock_info.assert_has_calls([
            call('Installing package package1'),
            call('Downloading script for package "package1" from "https://example.com/package1.sh"')
        ])

    def test_get_missing_dependencies(self):
        self.planner.steps = [
            Step(name='Step 1', dependencies=['command1', 'command2'], display_messages=display_messages, command='ls'),
            Step(name='Step 2', dependencies=['command3'], display_messages=display_messages, command='ls')
        ]
        with patch('planner.planner.shutil.which') as mock_which:
            mock_which.side_effect = [False, True, False]
            missing_dependencies = self.planner._ExecutionPlanner__get_missing_dependencies()
            self.assertEqual(missing_dependencies, {'command1', 'command3'})

    def test_get_step_effort(self):
        step1 = Step(
            name='Step 1',
            display_messages=display_messages,
            command='ls',
            on_success=Step(
                name='Step 1.1',
                display_messages=display_messages,
                command='ls',
                on_success=Step(
                    name='Step 1.1.1',
                    display_messages=display_messages,
                    command='ls'
                )
            )
        )
        step2 = Step(
            name='Step 2',
            display_messages=display_messages,
            command='ls',
            on_failure=Step(
                name='Step 2.1',
                display_messages=display_messages,
                command='ls',
                on_failure=Step(
                    name='Step 2.1.1',
                    display_messages=display_messages,
                    command='ls'
                )
            )
        )
        self.assertEqual(self.planner._ExecutionPlanner__get_step_effort(step1), 3)
        self.assertEqual(self.planner._ExecutionPlanner__get_step_effort(step2), 3)

    def test_get_plan_effort(self):
        self.planner.steps = [
            Step(name='Step 1', display_messages=display_messages, command='ls'),
            Step(name='Step 2', display_messages=display_messages, command='ls')
        ]
        self.assertEqual(self.planner._ExecutionPlanner__get_plan_effort(), 2)

    @patch.object(ExecutionPlanner, '_ExecutionPlanner__install_packages')
    @patch.object(ExecutionPlanner, '_ExecutionPlanner__get_plan_effort')
    @patch.object(ExecutionPlanner, '_ExecutionPlanner__get_missing_dependencies')
    def test_execute_with_missing_dependencies(self, mock_get_missing_dependencies, mock_get_plan_effort,
                                               mock_install_packages):
        mock_get_missing_dependencies.return_value = {'package1', 'package2'}
        mock_get_plan_effort.return_value = 5
        self.planner.steps = [
            Step(name='Step 1', dependencies=['command1'], display_messages=display_messages, command='ls'),
            Step(name='Step 2', dependencies=['command2'], display_messages=display_messages, command='ls')
        ]
        self.planner.execute()
        mock_get_missing_dependencies.assert_called_once()
        mock_get_plan_effort.assert_called_once()
        mock_install_packages.assert_called_once_with({'package1', 'package2'})

    @patch('planner.planner.logger.info')
    @patch.object(ExecutionPlanner, '_ExecutionPlanner__install_packages')
    @patch.object(ExecutionPlanner, '_ExecutionPlanner__get_plan_effort')
    @patch.object(ExecutionPlanner, '_ExecutionPlanner__get_missing_dependencies')
    def test_execute_without_missing_dependencies(self, mock_get_missing_dependencies, mock_get_plan_effort,
                                                  mock_install_packages, mock_info):
        mock_get_missing_dependencies.return_value = set()
        mock_get_plan_effort.return_value = 5
        self.planner.steps = [
            Step(name='Step 1', dependencies=['command1'], display_messages=display_messages, command='ls'),
            Step(name='Step 2', dependencies=['command2'], display_messages=display_messages, command='ls')
        ]
        self.planner.execute()
        mock_get_missing_dependencies.assert_called_once()
        mock_get_plan_effort.assert_called_once()
        mock_install_packages.assert_not_called()
        mock_info.assert_has_calls([
            call('Checking for missing dependencies'),
            call('Plan effort: 5'),
            call('No missing dependencies found'),
            call('Executing steps'),
            call('Executing step parent "Step 1"'),
            call('Step succeeded'),
            call('Executing step parent "Step 2"'),
            call('Step succeeded')
        ])

    @patch('planner.planner.Shell.execute_command')
    @patch.object(ExecutionPlanner, '_ExecutionPlanner__update_display_for_step_start')
    @patch.object(ExecutionPlanner, '_ExecutionPlanner__on_step_success')
    @patch.object(ExecutionPlanner, '_ExecutionPlanner__on_step_failure')
    def test_execute_step_success(self, mock_on_step_failure, mock_on_step_success, mock_update_display_for_step_start,
                                  mock_execute_command):
        mock_execute_command.return_value = ProcessResult(exit_code=0, stdout='', stderr='')
        step = Step(name='Step 1', command='command1', args=['arg1', 'arg2'], display_messages=DisplayMessages())
        self.planner._ExecutionPlanner__execute_step(step)
        mock_execute_command.assert_called_once_with(command=['command1', 'arg1', 'arg2'])
        mock_update_display_for_step_start.assert_called_once_with(step, 'parent')
        mock_on_step_success.assert_called_once_with(step)
        mock_on_step_failure.assert_not_called()

    @patch('planner.planner.Shell.execute_command')
    @patch.object(ExecutionPlanner, '_ExecutionPlanner__update_display_for_step_start')
    @patch.object(ExecutionPlanner, '_ExecutionPlanner__on_step_success')
    @patch.object(ExecutionPlanner, '_ExecutionPlanner__on_step_failure')
    def test_execute_step_failure(self, mock_on_step_failure, mock_on_step_success, mock_update_display_for_step_start,
                                  mock_execute_command):
        mock_execute_command.return_value = ProcessResult(exit_code=1, stdout='', stderr='')
        step = Step(name='Step 1', command='command1', args=['arg1', 'arg2'], display_messages=DisplayMessages())
        self.planner._ExecutionPlanner__execute_step(step)
        mock_execute_command.assert_called_once_with(command=['command1', 'arg1', 'arg2'])
        mock_update_display_for_step_start.assert_called_once_with(step, 'parent')
        mock_on_step_success.assert_not_called()
        mock_on_step_failure.assert_called_once_with(step, ProcessResult(exit_code=1, stdout='', stderr=''))


if __name__ == '__main__':
    unittest.main()
