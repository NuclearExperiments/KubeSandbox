from __future__ import annotations

import logging
import os
from typing import Literal

from pydantic import BaseModel
from rich.align import Align
from rich.console import ConsoleRenderable, RichCast, Group
from rich.layout import Layout
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, TaskID
from rich.status import Status
from rich.text import Text

logger = logging.getLogger('App.RichDisplay')


class PanelTheme(BaseModel):
    """
    Theme for a panel.

    Attributes:
        panel_style: The style of the panel.
        panel_content_style: The style of the content within the panel.
        panel_border_style: The style of the border of the panel.
    """
    panel_style: str
    panel_content_style: str
    panel_border_style: str


class DisplayTheme(BaseModel):
    """
    Theme for the display.

    Attributes:
        default_dark: The default dark color.
        default_light: The default light color.
        default_highlight: The default highlight color.
        spinner: The type of spinner to use.
        left_panel: The theme for the left panel.
        right_panel: The theme for the right panel.
        header_panel: The theme for the header panel.
        footer_panel: The theme for the footer panel.
        logs_panel: The theme for the logs panel.
        details_panel: The theme for the details panel.
    """
    default_dark: str = 'grey19'
    default_light: str = 'cyan1'
    default_highlight: str = 'bright_black'
    spinner: str = 'dots'

    left_panel: PanelTheme = PanelTheme(
        panel_style=default_dark,
        panel_content_style='black',
        panel_border_style=default_dark
    )

    right_panel: PanelTheme = PanelTheme(
        panel_style=default_dark,
        panel_content_style='black',
        panel_border_style=default_dark
    )
    header_panel: PanelTheme = PanelTheme(
        panel_style=default_dark,
        panel_content_style='bright_white',
        panel_border_style=default_highlight
    )
    footer_panel: PanelTheme = PanelTheme(
        panel_style=default_dark,
        panel_content_style='black',
        panel_border_style=default_highlight
    )
    logs_panel: PanelTheme = PanelTheme(
        panel_style='bright_white',
        panel_content_style='bright_black',
        panel_border_style='white'
    )
    details_panel: PanelTheme = PanelTheme(
        panel_style=default_light,
        panel_content_style='black',
        panel_border_style='cyan2'
    )


class RichDisplay:
    """
    A class for displaying information using Rich.

    Attributes:
        title: The title of the display.
        theme: The theme to use for the display.
    """

    def __init__(self, title: str, theme: DisplayTheme = DisplayTheme()):
        layout = Layout()

        layout.split_column(
            Layout(name='header', minimum_size=5, ratio=1),
            Layout(name='center', minimum_size=20, ratio=8),
            Layout(name='footer', minimum_size=5, ratio=1)
        )

        layout['center'].split_row(
            Layout(name='left', size=2),
            Layout(name='logs', minimum_size=40, ratio=6),
            Layout(name='details', minimum_size=40, ratio=4),
            Layout(name='right', size=2)
        )

        self.running = False
        self.theme = theme
        self.title_text: str = title
        self.layout: Layout = layout
        self.last_added_item: str | ConsoleRenderable | RichCast = ''
        self.live = Live(renderable=layout, refresh_per_second=60)

        self.logs_content = Group()
        self.progress = Progress()

        self.header_panel = self.get_standard_panel(self.title_text, self.theme.header_panel)
        self.footer_panel = self.get_standard_panel(self.progress, self.theme.footer_panel)
        self.left_panel = self.get_standard_panel('', self.theme.left_panel)
        self.right_panel = self.get_standard_panel('', self.theme.right_panel)
        self.details_panel = self.get_standard_panel('', self.theme.details_panel)
        self.logs_panel = self.get_standard_panel(self.logs_content, self.theme.logs_panel)

        self.layout['logs'].update(self.logs_panel)
        self.layout['details'].update(self.details_panel)
        self.layout['header'].update(self.header_panel)
        self.layout['footer'].update(self.footer_panel)
        self.layout['left'].update(self.left_panel)
        self.layout['right'].update(self.right_panel)

    @staticmethod
    def get_standard_panel(content: ConsoleRenderable | RichCast | str, theme: PanelTheme):
        """
        Creates a standard panel with the given content and theme.

        Args:
            content: The content to display in the panel.
            theme: The theme to use for the panel.

        Returns:
            A Panel object representing the standard panel.
        """
        return Panel(
            Align(content, align='center', vertical='middle'),
            style=f'{theme.panel_content_style} on {theme.panel_style}',
            border_style=theme.panel_border_style
        )

    def start(self):
        """
        Starts the live display.
        """
        if not self.running:
            os.system('clear')
            self.live.start()
            self.running = True

    def stop(self):
        """
        Stops the live display.
        """
        if self.running:
            self.live.stop()
            os.system('clear')
            self.running = False

    def push_to_logs(self, item: ConsoleRenderable | RichCast | str):
        """
        Pushes an item to the logs panel.

        Args:
            item: The item to push to the logs panel.
        """
        if isinstance(self.last_added_item, Status):
            logger.info('Stopping status loader')
            self.logs_content.renderables.pop()

        logger.info(f'Adding item {item}')
        self.last_added_item = item
        self.logs_content.renderables.append(item)

    def advance_progress_bar(self, task_id: int, advance_by: int):
        """
        Advances a progress bar by the given amount.

        Args:
            task_id: The ID of the progress bar to advance.
            advance_by: The amount to advance the progress bar by.
        """
        logger.debug(f'Advancing progress bar {task_id} by {advance_by}')
        self.progress.advance(TaskID(task_id), advance=advance_by)

    def add_progress_bar(self, title: str, total: int) -> int:
        """
        Adds a new progress bar to the display.

        Args:
            title: The title of the progress bar.
            total: The total value of the progress bar.

        Returns:
            The ID of the newly added progress bar.
        """
        logger.debug(f'Adding progress bar {title} with total {total}')
        task_id = self.progress.add_task(title, total=total)
        return int(task_id)

    def add_item_to_logs(self, text: str, item_type: Literal['loading', 'success', 'warning', 'error', 'heading']):
        """
        Adds an item to the logs panel with the specified type.

        Args:
            text: The text of the item to add.
            item_type: The type of item to add.
        """
        if item_type == 'loading':
            item = Status(Text.from_markup(f'[bold navy_blue]{text}[/]'), spinner=self.theme.spinner)
        elif item_type == 'success':
            item = Text.from_markup(text=f'[green]:white_check_mark: {text}[/]', justify='left')
        elif item_type == 'warning':
            item = Text.from_markup(text=f'[bright_yellow][bold] :bangbang: [/bold]{text}[/]', justify='left')
        elif item_type == 'error':
            item = Text.from_markup(text=f'[bright_red]:cross_mark: {text}[/]', justify='left')
        elif item_type == 'heading':
            item = Text.from_markup(text=f'[underline]\n{text}[/]\n', style='bold black', justify='center')

        self.push_to_logs(item)

    def set_details_message(self, message: str, print_raw: bool = False):
        """
        Sets the details message for the display.

        Args:
            message: The message to set.
            print_raw: Whether to print the message without formatting.
        """
        if not print_raw:
            message = Markdown(
                message,
                justify='center',
                style=self.theme.details_panel.panel_content_style
            )
        self.details_panel.renderable = Align(
            message,
            align='center',
            vertical='middle'
        )
