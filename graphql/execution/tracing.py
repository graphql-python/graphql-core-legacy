import time


class TracingMiddleware(object):
    DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

    def __init__(self):
        self.resolver_stats = list()
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = time.time() * 1000

    def end(self):
        self.end_time = time.time() * 1000

    @property
    def start_time_str(self):
        return time.strftime(self.DATETIME_FORMAT, time.gmtime(self.start_time/1000))

    @property
    def end_time_str(self):
        return time.strftime(self.DATETIME_FORMAT, time.gmtime(self.end_time/1000))

    @property
    def duration(self):
        if not self.end_time:
            raise ValueError("Tracing has not ended yet!")

        return (self.end_time - self.start_time)

    @property
    def tracing_dict(self):
        return dict(
            version=1,
            startTime=self.start_time_str,
            endTime=self.end_time_str,
            duration=self.duration,
            execution=dict(
                resolvers=self.resolver_stats
            )
        )

    def resolve(self, _next, root, info, *args, **kwargs):
        start = time.time()
        try:
            return _next(root, info, *args, **kwargs)
        finally:
            end = time.time()
            elapsed_ms = (end - start) * 1000

            stat = {
                "path": info.path,
                "parentType": str(info.parent_type),
                "fieldName": info.field_name,
                "returnType": str(info.return_type),
                "startOffset": (time.time() * 1000) - self.start_time,
                "duration": elapsed_ms,
            }
            self.resolver_stats.append(stat)
