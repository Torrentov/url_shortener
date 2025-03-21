from locust import HttpUser, task, between
import random
import string
import time


def random_url():
    path = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return f"https://example.com/{path}"

class URLShortenerUser(HttpUser):
    wait_time = between(0.3, 1.0)

    @task
    def full_link_lifecycle(self):
        response = self.client.post("/links/shorten", json={"original_url": random_url()})
        if response.status_code != 200:
            return

        data = response.json()
        short_code = data.get("short_code")
        if not short_code:
            return
        
        time.sleep(random.uniform(0.5, 2.0))

        self.client.get(f"/links/{short_code}", allow_redirects=False)

        time.sleep(random.uniform(0.5, 2.0))

        self.client.delete(f"/links/{short_code}")
