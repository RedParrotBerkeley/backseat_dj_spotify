from spotapi import Client
import logging

class SpotAPIHandler:
    def __init__(self, username: str, password: str):
        self.client = Client(username=username, password=password)
        logging.info("SpotAPI client initialized")

    def search_and_play(self, query: str):
        try:
            results = self.client.search(query)
            if results and results['tracks']['items']:
                uri = results['tracks']['items'][0]['uri']
                self.client.play(uri)
                logging.info(f"Playing: {query}")
            else:
                logging.warning(f"No results found for: {query}")
        except Exception as e:
            logging.error(f"Failed to play {query}: {str(e)}")
