import os

from .infrai import infrai


def schedule_weekly_digest() -> str:
    task_url = os.environ["DIGEST_TASK_URL"]
    return infrai.cron.create(cron_expr="0 8 * * 1", task=task_url)


if __name__ == "__main__":
    job_id = schedule_weekly_digest()
    print(f"Weekly legal digest scheduled as {job_id}")
