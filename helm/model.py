from typing import Optional

from pydantic import BaseModel

from planner.support import DisplayMessages
from storage import Resource


class HelmChart(BaseModel):
    """
    Helm chart model.
    """
    release_name: str
    chart: str
    repository_url: str = ''
    wait: bool = False
    timeout: Optional[str] = None
    namespace: Optional[str] = None
    values: Optional[dict] = None
    version: Optional[str] = None
    display_messages: Optional[DisplayMessages] = None
    resources: list[Resource] = []
