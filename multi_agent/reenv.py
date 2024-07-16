# copy and modify from:
# metagpt.environment.Environment(version:0.8.1)
# MAIN: add `record`

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : base env of executing environment


from typing import TYPE_CHECKING, Dict, Set

from pydantic import ConfigDict, Field, SerializeAsAny

from metagpt.context import Context
from metagpt.environment import Environment
from metagpt.logs import logger
from metagpt.schema import Message
from metagpt.utils.common import is_send_to

if TYPE_CHECKING:
    from metagpt.roles.role import Role  # noqa: F401


class RecordEnvironment(Environment):
    """环境，承载一批角色，角色可以向环境发布消息，可以被其他角色观察到
    Environment, hosting a batch of roles, roles can publish messages to the environment, and can be observed by other roles
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    desc: str = Field(default="")  # 环境描述
    roles: dict[str, SerializeAsAny["Role"]] = Field(default_factory=dict, validate_default=True)
    member_addrs: Dict["Role", Set] = Field(default_factory=dict, exclude=True)
    history: str = ""  # For debug
    record: dict = {}
    context: Context = Field(default_factory=Context, exclude=True)

    def publish_message(self, message: Message, peekable: bool = True) -> bool:
        """
        Distribute the message to the recipients.
        In accordance with the Message routing structure design in Chapter 2.2.1 of RFC 116, as already planned
        in RFC 113 for the entire system, the routing information in the Message is only responsible for
        specifying the message recipient, without concern for where the message recipient is located. How to
        route the message to the message recipient is a problem addressed by the transport framework designed
        in RFC 113.
        """
        logger.debug(f"publish_message: {message.dump()}")
        found = False
        # According to the routing feature plan in Chapter 2.2.3.2 of RFC 113
        for role, addrs in self.member_addrs.items():
            if is_send_to(message, addrs):
                role.put_message(message)
                found = True
        if not found:
            logger.warning(f"Message no recipients: {message.dump()}")
        
        self.record[message.role] = message.content
        self.history += f"\n{message}"  # For debug

        return True

RecordEnvironment.model_rebuild()
