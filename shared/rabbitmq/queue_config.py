from shared.rabbitmq.enums.queue_names import QueueNames

_all_channels = []

for name in QueueNames:
    _all_channels.append(name.value)

ALL_QUEUE_CHANNELS = _all_channels
