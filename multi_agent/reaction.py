# copy and modify from:
# metagpt.actions.Action(version:0.8.1)
# MAIN: set `stream = False` in _aask

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : action.py
"""

from __future__ import annotations

from typing import Optional, Union

from pydantic import ConfigDict, Field

from metagpt.actions import Action
from metagpt.actions.action_node import ActionNode
from metagpt.schema import (
    CodePlanAndChangeContext,
    CodeSummarizeContext,
    CodingContext,
    RunCodeContext,
    TestingContext,
)
from metagpt.utils.project_repo import ProjectRepo


class ReAction(Action):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = ""
    i_context: Union[
        dict, CodingContext, CodeSummarizeContext, TestingContext, RunCodeContext, CodePlanAndChangeContext, str, None
    ] = ""
    prefix: str = ""  # aask*时会加上prefix，作为system_message
    desc: str = ""  # for skill manager
    node: ActionNode = Field(default=None, exclude=True)

    async def _aask(self, prompt: str, system_msgs: Optional[list[str]] = None,stream:bool=False) -> str:
        """Append default prefix"""
        return await self.llm.aask(prompt, system_msgs,stream=stream)
