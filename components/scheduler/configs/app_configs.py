from dataclasses import asdict, dataclass
from shared.rabbitmq.enums.queue_names import QueueNames

# SCHEDULER_QUEUE_CHANNELS = {
#     # consumes
#     'crawlresult': QueueNames.PARSE.value,
#     'processlinks': QueueNames.CRAWL.value,
#     # produces
#     'crawl': QueueNames.CRAWL.value,
#     'storelinks': QueueNames.FAILED_TASK.value
# }

# TODO: Cleanup all these unneed configs afterwards


@dataclass(frozen=True)
class SchedulerQueueChannels:
    # consumes
    crawlresult: str = QueueNames.PARSE.value
    processlinks: str = QueueNames.CRAWL_TASK.value

    # produces
    crawl: str = QueueNames.CRAWL_TASK.value
    storelinks: str = QueueNames.FAILED_TASK.value

    def values(self) -> list[str]:
        return list(asdict(self).values())


SCHEDULER_QUEUE_CHANNELS = SchedulerQueueChannels()
