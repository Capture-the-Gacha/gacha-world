from typing import Counter
from locust import HttpUser, events, task
import logging
import random
import string
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GachaUser(HttpUser):
    rarities_count = Counter()
    
    def on_start(self):
        # Generate random username and password
        username = ''.join(random.choices(string.ascii_letters, k=16))
        password = 'HardPassword123!'
        # Register the user and obtain response
        response = self.client.post("/register", json={"username": username, "password": password}, verify=False)
        if response.status_code == 200:
            self.id = response.json().get("player_id")
        else:
            logging.error(f"Registration failed with status {response.status_code}: {response.text}")
            raise Exception("Registration failed")

        # Authenticate and store the token
        response = self.client.post("/login", json={"username": username, "password": password}, verify=False)
        if response.status_code == 200:
            self.token = response.json().get("token")
        else:
            logging.error(f"Login failed with status {response.status_code}: {response.text}")
            raise Exception("Authentication failed")
        
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self.gachas = self.client.get("/gachas", verify=False, headers=headers).json()
        
        self.recharge()

    @task()
    def roll_gacha(self):
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        response = self.client.get(f"/roll", headers=headers, verify=False)
        if response.status_code == 200:
            data = response.json()
            gacha_id = data.get("gacha_id")
            gacha = next((x for x in self.gachas if x.get('id') == gacha_id), None)
            rarity = gacha.get('rarity') if gacha else None
            if rarity:
                GachaUser.rarities_count[rarity] += 1

    @task()
    def recharge(self):
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self.client.post(f"/recharge/{self.id}/{1_000_000}", headers=headers, verify=False)

    @task()
    def gachas(self):
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        self.client.get(f"/gachas", headers=headers, verify=False)

    
                    
@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    total = sum(GachaUser.rarities_count.values())
    print(total)
    if total > 0:
        logging.info(f"Final Rarity Distribution (total: {total}):")
        for rarity, count in GachaUser.rarities_count.items():
            percentage = (count / total) * 100 if total > 0 else 0
            logging.info(f"{rarity}: {count} ({percentage:.2f}%)")