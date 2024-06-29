from unittest.mock import MagicMock, patch

import pytest

from kubesandbox.exception_classes import UnknownPackageException, InstallationFailedException, \
    ExecutionFailureException
from kubesandbox.planner.planner import ExecutionPlanner
from kubesandbox.planner.support import Step, InstallationSource, DisplayMessages
from kubesandbox.shellclient.base_shell import ProcessResult

# Sample data for testing
sample_display_messages = DisplayMessages(
    success_message="Success",
    failure_message="Failure",
    ongoing_message="Ongoing",
    description="This is a test step",
    success_instructions="Follow these instructions on success",
    failure_instructions="Follow these instructions on failure"
)

sample_step = Step(
    name='sample_step',
    command='echo',
    args=['Hello'],
    display_messages=sample_display_messages
)

sample_installation_source = InstallationSource(
    url='http://example.com',
    request_params={},
    request_headers={}
)


# Mock classes
class MockShell:
    def execute_command(self, *args, **kwargs):
        return ProcessResult(stdout='success', stderr='', exit_code=0)


class MockRichDisplay:
    def __init__(self, *args, **kwargs):
        pass

    def add_item_to_logs(self, *args, **kwargs):
        pass

    def advance_progress_bar(self, *args, **kwargs):
        pass

    def set_details_message(self, *args, **kwargs):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def add_progress_bar(self, *args, **kwargs):
        return 1


# Test __init__ method
@patch('kubesandbox.planner.planner.Shell', new_callable=lambda: MockShell)
@patch('kubesandbox.planner.planner.RichDisplay', new_callable=lambda: MockRichDisplay)
def test_init(MockShellClass, MockRichDisplayClass):
    steps = [sample_step]
    installation_sources = {'sample_package': sample_installation_source}
    planner = ExecutionPlanner(steps=steps, installation_sources=installation_sources)
    assert planner.steps == [sample_step]
    assert isinstance(planner._shell, MockShell)
    assert isinstance(planner._display, MockRichDisplay)
    assert planner.installation_sources == {'sample_package': sample_installation_source}
    assert planner.progress_id == 0
    assert planner.current_step_total_effort == 0
    assert planner.current_step_spent_effort == 0


# Test __download_package_installation_script method
@patch('kubesandbox.planner.planner.Shell', new_callable=lambda: MockShell)
@patch('kubesandbox.planner.planner.RichDisplay', new_callable=lambda: MockRichDisplay)
@patch('httpx.get')
def test_download_package_installation_script(mock_httpx_get, MockShellClass, MockRichDisplayClass):
    mock_httpx_get.return_value = MagicMock(status_code=200, text='installation_script')
    steps = [sample_step]
    installation_sources = {'sample_package': sample_installation_source}
    planner = ExecutionPlanner(steps=steps, installation_sources=installation_sources)
    script = planner._ExecutionPlanner__download_package_installation_script('sample_package')
    assert script == 'installation_script'

    mock_httpx_get.return_value = MagicMock(status_code=404)
    with pytest.raises(InstallationFailedException):
        planner._ExecutionPlanner__download_package_installation_script('sample_package')


# Test __execute_package_installation_script method
@patch('kubesandbox.planner.planner.Shell', new_callable=lambda: MockShell)
@patch('kubesandbox.planner.planner.RichDisplay', new_callable=lambda: MockRichDisplay)
def test_execute_package_installation_script(MockShellClass, MockRichDisplayClass):
    steps = [sample_step]
    installation_sources = {'sample_package': sample_installation_source}
    planner = ExecutionPlanner(steps=steps, installation_sources=installation_sources)

    with patch.object(planner._shell, 'execute_command',
                      return_value=ProcessResult(stdout='success', stderr='', exit_code=0)):
        planner._ExecutionPlanner__execute_package_installation_script('sample_package', 'installation_script')

    with patch.object(planner._shell, 'execute_command',
                      return_value=ProcessResult(stdout='fail', stderr='error', exit_code=1)):
        with pytest.raises(InstallationFailedException):
            planner._ExecutionPlanner__execute_package_installation_script('sample_package', 'installation_script')


# Test __install_package method
@patch('kubesandbox.planner.planner.Shell', new_callable=lambda: MockShell)
@patch('kubesandbox.planner.planner.RichDisplay', new_callable=lambda: MockRichDisplay)
def test_install_package(MockShellClass, MockRichDisplayClass):
    steps = [sample_step]
    installation_sources = {'sample_package': sample_installation_source}
    planner = ExecutionPlanner(steps=steps, installation_sources=installation_sources)

    with patch.object(planner, '_ExecutionPlanner__download_package_installation_script',
                      return_value='installation_script'), \
            patch.object(planner, '_ExecutionPlanner__execute_package_installation_script'):
        planner._ExecutionPlanner__install_package('sample_package')

    with pytest.raises(UnknownPackageException):
        planner._ExecutionPlanner__install_package('unknown_package')


# Test __install_packages method
@patch('kubesandbox.planner.planner.Shell', new_callable=lambda: MockShell)
@patch('kubesandbox.planner.planner.RichDisplay', new_callable=lambda: MockRichDisplay)
def test_install_packages(MockShellClass, MockRichDisplayClass):
    steps = [sample_step]
    installation_sources = {'sample_package': sample_installation_source}
    planner = ExecutionPlanner(steps=steps, installation_sources=installation_sources)

    with patch.object(planner._shell, 'execute_command',
                      return_value=ProcessResult(stdout='root', stderr='', exit_code=0)), \
            patch.object(planner, '_ExecutionPlanner__install_package'):
        planner._ExecutionPlanner__install_packages({'sample_package'})

    with patch.object(planner._shell, 'execute_command',
                      return_value=ProcessResult(stdout='', stderr='error', exit_code=1)):
        with pytest.raises(ExecutionFailureException):
            planner._ExecutionPlanner__install_packages({'sample_package'})


# Test __get_missing_dependencies method
@patch('kubesandbox.planner.planner.Shell', new_callable=lambda: MockShell)
@patch('kubesandbox.planner.planner.RichDisplay', new_callable=lambda: MockRichDisplay)
def test_get_missing_dependencies(MockShellClass, MockRichDisplayClass):
    steps = [sample_step]
    installation_sources = {'sample_package': sample_installation_source}
    planner = ExecutionPlanner(steps=steps, installation_sources=installation_sources)

    with patch('shutil.which', return_value=None):
        assert planner._ExecutionPlanner__get_missing_dependencies() == set(sample_step.dependencies)


# Test __get_step_effort method
@patch('kubesandbox.planner.planner.Shell', new_callable=lambda: MockShell)
@patch('kubesandbox.planner.planner.RichDisplay', new_callable=lambda: MockRichDisplay)
def test_get_step_effort(MockShellClass, MockRichDisplayClass):
    steps = [sample_step]
    installation_sources = {'sample_package': sample_installation_source}
    planner = ExecutionPlanner(steps=steps, installation_sources=installation_sources)

    step = Step(name='test_step', on_success=sample_step, command='ls', display_messages=sample_display_messages)
    assert planner._ExecutionPlanner__get_step_effort(step) == 2


# Test __get_plan_effort method
@patch('kubesandbox.planner.planner.Shell', new_callable=lambda: MockShell)
@patch('kubesandbox.planner.planner.RichDisplay', new_callable=lambda: MockRichDisplay)
def test_get_plan_effort(MockShellClass, MockRichDisplayClass):
    steps = [sample_step]
    installation_sources = {'sample_package': sample_installation_source}
    planner = ExecutionPlanner(steps=steps, installation_sources=installation_sources)

    assert planner._ExecutionPlanner__get_plan_effort() == 1


# Test execute method
@patch('kubesandbox.planner.planner.Shell', new_callable=lambda: MockShell)
@patch('kubesandbox.planner.planner.RichDisplay', new_callable=lambda: MockRichDisplay)
@patch('httpx.get')
def test_execute(mock_httpx_get, MockShellClass, MockRichDisplayClass):
    mock_httpx_get.return_value = MagicMock(status_code=200, text='installation_script')
    steps = [sample_step]
    installation_sources = {'sample_package': sample_installation_source}
    planner = ExecutionPlanner(steps=steps, installation_sources=installation_sources)

    with patch.object(planner, '_ExecutionPlanner__get_missing_dependencies', return_value=set()), \
            patch.object(planner, '_ExecutionPlanner__get_plan_effort', return_value=1), \
            patch.object(planner, '_ExecutionPlanner__execute_step'):
        planner.execute()


# Test __execute_step method
@patch('kubesandbox.planner.planner.Shell', new_callable=lambda: MockShell)
@patch('kubesandbox.planner.planner.RichDisplay', new_callable=lambda: MockRichDisplay)
def test_execute_step(MockShellClass, MockRichDisplayClass):
    steps = [sample_step]
    installation_sources = {'sample_package': sample_installation_source}
    planner = ExecutionPlanner(steps=steps, installation_sources=installation_sources)

    with patch.object(planner, '_ExecutionPlanner__update_display_for_step_start'), \
            patch.object(planner, '_ExecutionPlanner__execute_step'):
        planner._ExecutionPlanner__execute_step(sample_step)


# Test __on_step_failure method
@patch('kubesandbox.planner.planner.Shell', new_callable=lambda: MockShell)
@patch('kubesandbox.planner.planner.RichDisplay', new_callable=lambda: MockRichDisplay)
def test_on_step_failure(MockShellClass, MockRichDisplayClass):
    steps = [sample_step]
    installation_sources = {'sample_package': sample_installation_source}
    planner = ExecutionPlanner(steps=steps, installation_sources=installation_sources)

    result = ProcessResult(stdout='output', stderr='error', exit_code=1)
    with pytest.raises(ExecutionFailureException):
        planner._ExecutionPlanner__on_step_failure(sample_step, result)


# Test __on_step_success method
@patch('kubesandbox.planner.planner.Shell', new_callable=lambda: MockShell)
@patch('kubesandbox.planner.planner.RichDisplay', new_callable=lambda: MockRichDisplay)
def test_on_step_success(MockShellClass, MockRichDisplayClass):
    steps = [sample_step]
    installation_sources = {'sample_package': sample_installation_source}
    planner = ExecutionPlanner(steps=steps, installation_sources=installation_sources)

    with patch.object(planner, '_ExecutionPlanner__execute_step'):
        planner._ExecutionPlanner__on_step_success(sample_step)


# Test __update_display_for_step_start method
@patch('kubesandbox.planner.planner.Shell', new_callable=lambda: MockShell)
@patch('kubesandbox.planner.planner.RichDisplay', new_callable=lambda: MockRichDisplay)
def test_update_display_for_step_start(MockShellClass, MockRichDisplayClass):
    steps = [sample_step]
    installation_sources = {'sample_package': sample_installation_source}
    planner = ExecutionPlanner(steps=steps, installation_sources=installation_sources)

    with patch.object(planner._display, 'add_item_to_logs'), \
            patch.object(planner._display, 'set_details_message'), \
            patch.object(planner._display, 'start'):
        planner._ExecutionPlanner__update_display_for_step_start(sample_step, 'parent')


# Test __rectify_progress method
@patch('kubesandbox.planner.planner.Shell', new_callable=lambda: MockShell)
@patch('kubesandbox.planner.planner.RichDisplay', new_callable=lambda: MockRichDisplay)
def test_rectify_progress(MockShellClass, MockRichDisplayClass):
    steps = [sample_step]
    installation_sources = {'sample_package': sample_installation_source}
    planner = ExecutionPlanner(steps=steps, installation_sources=installation_sources)
    planner.current_step_total_effort = 2
    planner.current_step_spent_effort = 1

    with patch.object(planner._display, 'advance_progress_bar'):
        planner._ExecutionPlanner__rectify_progress()

    planner.current_step_total_effort = 1
    planner.current_step_spent_effort = 0

    with patch.object(planner._display, 'advance_progress_bar'):
        planner._ExecutionPlanner__rectify_progress()


# Test full coverage of ExecutionPlanner class
@patch('kubesandbox.planner.planner.Shell', new_callable=lambda: MockShell)
@patch('kubesandbox.planner.planner.RichDisplay', new_callable=lambda: MockRichDisplay)
@patch('httpx.get')
def test_execution_planner_full_coverage(mock_httpx_get, MockShellClass, MockRichDisplayClass):
    mock_httpx_get.return_value = MagicMock(status_code=200, text='installation_script')
    steps = [sample_step]
    installation_sources = {'sample_package': sample_installation_source}
    planner = ExecutionPlanner(steps=steps, installation_sources=installation_sources)

    with patch.object(planner, '_ExecutionPlanner__get_missing_dependencies', return_value={'sample_package'}), \
            patch.object(planner, '_ExecutionPlanner__get_plan_effort', return_value=1), \
            patch.object(planner, '_ExecutionPlanner__execute_step'), \
            patch.object(planner._shell, 'execute_command',
                         return_value=ProcessResult(stdout='root', stderr='', exit_code=0)), \
            patch.object(planner, '_ExecutionPlanner__install_package'), \
            patch.object(planner._display, 'start'), \
            patch.object(planner._display, 'stop'):
        planner.execute()

        assert planner._ExecutionPlanner__get_missing_dependencies.called
        assert planner._ExecutionPlanner__get_plan_effort.called
        assert planner._ExecutionPlanner__execute_step.called
        assert planner._shell.execute_command.called
        assert planner._ExecutionPlanner__install_package.called
        assert planner._display.start.called
        assert planner._display.stop.called

        assert planner._ExecutionPlanner__get_step_effort(sample_step) == 1
        assert planner._ExecutionPlanner__get_plan_effort() == 1
        assert planner._ExecutionPlanner__download_package_installation_script('sample_package') == 'installation_script'
        assert planner._ExecutionPlanner__execute_package_installation_script('sample_package',
                                                                              'installation_script') is None
        planner._ExecutionPlanner__install_package.assert_called_once_with('sample_package')
        assert planner._ExecutionPlanner__on_step_success(sample_step) is None
        assert planner._ExecutionPlanner__update_display_for_step_start(sample_step, 'parent') is None
        assert planner._ExecutionPlanner__rectify_progress() is None

@patch('kubesandbox.planner.planner.Shell', new_callable=lambda: MockShell)
@patch('kubesandbox.planner.planner.RichDisplay', new_callable=lambda: MockRichDisplay)
@patch('httpx.get')
def test_execution_planner_full_coverage_missing_dependencies(mock_httpx_get, MockShellClass, MockRichDisplayClass):
    mock_httpx_get.return_value = MagicMock(status_code=200, text='installation_script')
    steps = [sample_step]
    installation_sources = {'sample_package': sample_installation_source}
    planner = ExecutionPlanner(steps=steps, installation_sources=installation_sources)

    with patch.object(planner, '_ExecutionPlanner__get_missing_dependencies', return_value=set()), \
            patch.object(planner, '_ExecutionPlanner__get_plan_effort', return_value=1), \
            patch.object(planner, '_ExecutionPlanner__execute_step'), \
            patch.object(planner._shell, 'execute_command',
                         return_value=ProcessResult(stdout='root', stderr='', exit_code=0)), \
            patch.object(planner, '_ExecutionPlanner__install_package'), \
            patch.object(planner._display, 'start'), \
            patch.object(planner._display, 'stop'):
        planner.execute()

        assert planner._ExecutionPlanner__get_missing_dependencies.called
        assert planner._ExecutionPlanner__get_plan_effort.called
        assert planner._ExecutionPlanner__execute_step.called
        assert not planner._shell.execute_command.called
        assert not planner._ExecutionPlanner__install_package.called
        assert planner._display.start.called
        assert planner._display.stop.called

        assert planner._ExecutionPlanner__get_step_effort(sample_step) == 1
        assert planner._ExecutionPlanner__get_plan_effort() == 1
        assert planner._ExecutionPlanner__download_package_installation_script('sample_package') == 'installation_script'
        assert planner._ExecutionPlanner__execute_package_installation_script('sample_package',
                                                                              'installation_script') is None
        assert planner._ExecutionPlanner__on_step_success(sample_step) is None
        assert planner._ExecutionPlanner__update_display_for_step_start(sample_step, 'parent') is None
        assert planner._ExecutionPlanner__rectify_progress() is None
