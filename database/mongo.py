"""MongoDB connection and query operations."""

from typing import Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from config import config


class MongoDatabase:
    """MongoDB connection manager and query interface."""

    def __init__(self):
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None
        self._collection: Optional[Collection] = None

    def connect(self) -> None:
        """Establish connection to MongoDB."""
        self._client = MongoClient(config.MONGODB_URI)
        self._db = self._client[config.MONGODB_DATABASE]
        self._collection = self._db[config.EMPLOYEES_COLLECTION]

    def close(self) -> None:
        """Close MongoDB connection."""
        if self._client:
            self._client.close()

    @property
    def collection(self) -> Collection:
        """Get the employees collection."""
        if self._collection is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._collection

    def get_employee(self, name: str) -> Optional[dict]:
        """
        Fetch a single employee by name.

        Args:
            name: Employee name to search for (case-insensitive).

        Returns:
            Employee document or None if not found.
        """
        return self.collection.find_one(
            {"name": {"$regex": f"^{name}$", "$options": "i"}}
        )

    def get_all_employees(self) -> list[dict]:
        """
        Fetch all employees from the database.

        Returns:
            List of employee documents.
        """
        return list(self.collection.find())

    def list_employee_names(self) -> list[str]:
        """
        Get a list of all employee names.

        Returns:
            List of employee names.
        """
        employees = self.collection.find({}, {"name": 1, "_id": 0})
        return [emp["name"] for emp in employees]

    def insert_employee(self, employee_data: dict) -> str:
        """
        Insert a new employee into the database.

        Args:
            employee_data: Employee document to insert.

        Returns:
            Inserted document ID as string.
        """
        result = self.collection.insert_one(employee_data)
        return str(result.inserted_id)

    def update_employee(self, name: str, update_data: dict) -> bool:
        """
        Update an existing employee.

        Args:
            name: Employee name to update.
            update_data: Fields to update.

        Returns:
            True if updated, False if not found.
        """
        result = self.collection.update_one(
            {"name": {"$regex": f"^{name}$", "$options": "i"}},
            {"$set": update_data}
        )
        return result.modified_count > 0

    def delete_employee(self, name: str) -> bool:
        """
        Delete an employee from the database.

        Args:
            name: Employee name to delete.

        Returns:
            True if deleted, False if not found.
        """
        result = self.collection.delete_one(
            {"name": {"$regex": f"^{name}$", "$options": "i"}}
        )
        return result.deleted_count > 0

    def employee_exists(self, name: str) -> bool:
        """
        Check if an employee exists.

        Args:
            name: Employee name to check.

        Returns:
            True if exists, False otherwise.
        """
        return self.get_employee(name) is not None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
