´import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from gridfs import GridFS
from bson import ObjectId
import json
import logging

from config import PARTICIPANTS_FILE

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Handles MongoDB connections with GridFS and falls back to JSON files."""

    def __init__(self):
        # Read MongoDB URI from environment variable or .env file
        self.mongo_uri = os.getenv("MONGODB_URI")
        self.client = None
        self.db = None
        self.fs = None
        self.connected = False

        if self.mongo_uri:
            self._connect()
        else:
            logger.warning(
                "MONGODB_URI not set. Falling back to local JSON storage.")

    def _connect(self):
        """Try to establish a connection to MongoDB and initialise GridFS."""
        try:
            self.client = MongoClient(
                self.mongo_uri, serverSelectionTimeoutMS=5000)
            # Ping the server to confirm connection.
            self.client.admin.command("ping")
            self.db = self.client.get_default_database()
            self.fs = GridFS(self.db)
            self.connected = True
            logger.info("Successfully connected to MongoDB.")
        except ConnectionFailure as exc:
            logger.warning(
                "MongoDB connection failed: %s. Falling back to JSON.", exc)
            self.connected = False

    def is_connected(self):
        """Check if MongoDB is connected"""
        return self.client is not None

    # Participant helpers ------------------------------------------------------------------

    def get_participants(self):
        """Return all participants as list of dicts."""
        if self.connected and self.db is not None:
            participants = list(self.db.participants.find({}, {"_id": False}))
            logger.debug("Fetched %s participants from MongoDB",
                         len(participants))
            return participants

        # Fallback to JSON file
        if os.path.exists(PARTICIPANTS_FILE):
            with open(PARTICIPANTS_FILE, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    logger.debug(
                        "Fetched %s participants from JSON", len(data))
                    return data
                except json.JSONDecodeError:
                    logger.error(
                        "Invalid JSON in participants file. Returning empty list.")
        return []

    def save_participant(self, participant: dict):
        """Persist a single participant."""
        if self.connected and self.db is not None:
            self.db.participants.insert_one(participant)
            logger.debug("Saved participant to MongoDB: %s",
                         participant.get("email"))
            return

        # Fallback -> append to JSON file
        participants = self.get_participants()
        participants.append(participant)
        with open(PARTICIPANTS_FILE, "w", encoding="utf-8") as f:
            json.dump(participants, f, ensure_ascii=False, indent=2)
        logger.debug("Saved participant to JSON file: %s",
                     participant.get("email"))

    # GridFS helpers ---------------------------------------------------------------------

    def store_file(self, file_obj, filename: str):
        """Store a file in GridFS. Returns the file_id or None if fallback."""
        if self.connected and self.fs is not None:
            file_id = self.fs.put(file_obj, filename=filename)
            logger.debug("Stored file %s in GridFS with id %s",
                         filename, str(file_id))
            return str(file_id)
        logger.warning(
            "store_file called but MongoDB/FS not available. No-op.")
        return None

    def retrieve_file(self, file_id, destination: str):
        """Retrieve a file from GridFS and write it to destination path."""
        if self.connected and self.fs is not None:
            grid_out = self.fs.get(file_id)
            with open(destination, "wb") as f:
                f.write(grid_out.read())
            logger.debug("Retrieved file id %s to %s",
                         str(file_id), destination)
            return destination
        logger.warning(
            "retrieve_file called but MongoDB/FS not available. No-op.")
        return None


# Instantiate a global manager so other modules can just import it

db_manager = DatabaseManager()
