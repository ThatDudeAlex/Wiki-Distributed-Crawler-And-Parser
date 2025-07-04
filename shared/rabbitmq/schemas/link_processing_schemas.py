from dataclasses import dataclass
from shared.rabbitmq.types import QueueMsgSchemaInterface
from shared.rabbitmq.schemas.parsing_task_schemas import LinkData, ProcessDiscoveredLinks


# === Save Link Record (Scheduler → DB Writer) ===

@dataclass
class SaveProcessedLinks(ProcessDiscoveredLinks):
    # Only inherits from ProcessDiscoveredLinks beccause it's
    # semantically different but structurally the same
    pass
