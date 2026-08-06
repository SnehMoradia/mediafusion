import os
from tasks import celery_app

if __name__ == '__main__':
    celery_app.start(['worker', '--loglevel=info', '--concurrency=4'])
