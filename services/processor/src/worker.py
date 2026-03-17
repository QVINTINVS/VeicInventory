import os

from redis import Redis
from rq import Worker

redis_url = os.getenv("REDIS_URL")

conn = Redis.from_url(redis_url)

if __name__ == "__main__":
    print("RQ worker iniciado")

    worker = Worker(("emission_queue",), connection=conn)
    worker.work(with_scheduler=True)
