from shared.config import QueueNames

PARSER_QUEUE_CHANNELS = {
    'listen': QueueNames.PARSE.value,
    'savecontent': QueueNames.SAVE_CONTENT.value,
    'enqueuelinks': QueueNames.ENQUEUE_LINKS.value,
    'failed': QueueNames.FAILED_TASK.value
}
