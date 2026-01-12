"""MongoDB connection and query operations."""

from datetime import datetime
from typing import Optional
from bson import ObjectId
from pymongo import MongoClient, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database

from config import config


class MongoDatabase:
    """MongoDB connection manager and query interface."""

    def __init__(self):
        self._client: Optional[MongoClient] = None
        self._db: Optional[Database] = None
        self._collection: Optional[Collection] = None
        self._templates: Optional[Collection] = None
        self._reviews: Optional[Collection] = None
        self._audit_logs: Optional[Collection] = None

    def connect(self) -> None:
        """Establish connection to MongoDB."""
        self._client = MongoClient(config.MONGODB_URI)
        self._db = self._client[config.MONGODB_DATABASE]
        self._collection = self._db[config.EMPLOYEES_COLLECTION]
        self._templates = self._db["review_templates"]
        self._reviews = self._db["reviews"]
        self._audit_logs = self._db["audit_logs"]
        self._init_default_templates()

    def close(self) -> None:
        """Close MongoDB connection."""
        if self._client:
            self._client.close()

    @property
    def collection(self) -> Collection:
        """Get the employees' collection."""
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

    def add_review_to_employee(self, employee_name: str, review_id: str) -> bool:
        """Add a review ID to employee's reviews array."""
        result = self.collection.update_one(
            {"name": {"$regex": f"^{employee_name}$", "$options": "i"}},
            {"$push": {"review_ids": ObjectId(review_id)}}
        )
        return result.modified_count > 0

    def get_employee_reviews(self, employee_name: str) -> list[dict]:
        """Get all reviews for an employee."""
        employee = self.get_employee(employee_name)
        if not employee or "review_ids" not in employee:
            return []
        review_ids = employee.get("review_ids", [])
        reviews = list(self._reviews.find({"_id": {"$in": review_ids}}).sort("generated_at", DESCENDING))
        for r in reviews:
            r["_id"] = str(r["_id"])
            if "employee_id" in r:
                r["employee_id"] = str(r["employee_id"])
        return reviews

    # =========================================================================
    # TEMPLATES COLLECTION
    # =========================================================================

    @property
    def templates(self) -> Collection:
        """Get the templates' collection."""
        if self._templates is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._templates

    def _init_default_templates(self) -> None:
        """Initialize default templates if collection is empty."""
        if self._templates.count_documents({}) > 0:
            return

        default_templates = [
            {
                "name": "formal",
                "display_name": "Formal Corporate",
                "description": "Traditional corporate HR style - professional, objective, third-person",
                "best_for": "Official HR records, large corporations, formal review processes",
                "active": True,
                "system_prompt": """You are a senior HR professional drafting formal performance reviews.
Generate professional, objective, and balanced content suitable for official HR records.
Use formal language and third-person perspective.
Be SPECIFIC - reference exact numbers, project names, and metrics from the data.
Maintain a professional, respectful tone throughout.""",
                "sections": """
Generate these sections using the data above. Use formal third-person language:

1. EXECUTIVE SUMMARY (2-3 paragraphs - formal assessment of overall performance)

2. KEY ACCOMPLISHMENTS (4-5 bullets - measurable achievements with business impact)

3. GOAL ATTAINMENT REVIEW (assess each previous goal with formal status)

4. DEVELOPMENT OPPORTUNITIES (2-3 areas for professional growth)

5. OBJECTIVES FOR NEXT REVIEW PERIOD (3-4 SMART goals aligned with business needs)

6. COMPETENCY ASSESSMENT QUESTIONS (3 role-specific evaluation questions)

7. LEADERSHIP POTENTIAL INDICATORS (3 questions assessing growth potential)

Use markdown formatting with ## headers. Maintain formal corporate tone.""",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
            {
                "name": "casual",
                "display_name": "Casual Friendly",
                "description": "Modern friendly style - warm, encouraging, first-person",
                "best_for": "Startups, small teams, regular check-ins",
                "active": True,
                "system_prompt": """You are a friendly team lead writing a performance check-in.
Generate warm, encouraging, and genuine feedback that feels personal.
Use first-person perspective and conversational language.
Be SPECIFIC - reference exact numbers, project names, and wins from the data.
Keep the tone supportive and growth-focused, like talking to a valued teammate.""",
                "sections": """
Generate these sections using the data above. Use friendly, first-person language:

1. THE BIG PICTURE (2-3 paragraphs - genuine reflection on their journey this quarter)

2. WINS WORTH CELEBRATING (4-5 bullets - highlight achievements with enthusiasm)

3. HOW'D THOSE GOALS GO? (friendly check-in on each previous goal)

4. ROOM TO GROW (2-3 growth areas framed as exciting opportunities)

5. WHAT'S NEXT? (3-4 goals framed as exciting challenges ahead)

6. SKILLS DEEP-DIVE (3 questions to explore their technical growth)

7. TEAM DYNAMICS CHECK (3 questions about collaboration and communication)

Use markdown formatting with ## headers. Keep it warm and encouraging!""",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
            {
                "name": "technical",
                "display_name": "Technical Engineering",
                "description": "Engineering-focused style - metrics-heavy, precise, technical",
                "best_for": "Engineering teams, technical roles, performance benchmarking",
                "active": True,
                "system_prompt": """You are a technical engineering manager writing a performance review.
Generate detailed, metrics-driven, and technically-focused content.
Emphasize code quality, system impact, and technical decision-making.
Be SPECIFIC - reference exact commit counts, latency improvements, and technical achievements.
Use precise technical language appropriate for engineering documentation.""",
                "sections": """
Generate these sections using the data above. Focus on technical metrics and impact:

1. TECHNICAL PERFORMANCE OVERVIEW (2-3 paragraphs - emphasize system impact and code quality)

2. ENGINEERING ACHIEVEMENTS (4-5 bullets - include specific metrics: latency, throughput, uptime)

3. GOAL COMPLETION METRICS (assess each goal with quantitative outcomes)

4. TECHNICAL DEBT & GROWTH VECTORS (2-3 specific technical areas for improvement)

5. ENGINEERING OBJECTIVES Q+1 (3-4 technically-scoped, measurable goals)

6. TECHNICAL ASSESSMENT (3 architecture/design questions based on their stack)

7. ENGINEERING LEADERSHIP (3 questions on mentorship, code review, and technical decisions)

Use markdown formatting with ## headers. Include specific numbers and technical details.""",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            },
        ]
        self._templates.insert_many(default_templates)

    def get_template(self, name: str) -> Optional[dict]:
        """Get a template by name."""
        template = self._templates.find_one({"name": name, "active": True})
        if template:
            template["_id"] = str(template["_id"])
        return template

    def get_all_templates(self, active_only: bool = True) -> list[dict]:
        """Get all templates."""
        query = {"active": True} if active_only else {}
        templates = list(self._templates.find(query))
        for t in templates:
            t["_id"] = str(t["_id"])
        return templates

    def create_template(self, template_data: dict) -> str:
        """Create a new template."""
        template_data["created_at"] = datetime.utcnow()
        template_data["updated_at"] = datetime.utcnow()
        template_data["active"] = template_data.get("active", True)
        result = self._templates.insert_one(template_data)
        return str(result.inserted_id)

    def update_template(self, name: str, update_data: dict) -> bool:
        """Update an existing template."""
        update_data["updated_at"] = datetime.utcnow()
        result = self._templates.update_one(
            {"name": name},
            {"$set": update_data}
        )
        return result.modified_count > 0

    def delete_template(self, name: str) -> bool:
        """Soft delete a template (set active=False)."""
        result = self._templates.update_one(
            {"name": name},
            {"$set": {"active": False, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    # =========================================================================
    # REVIEWS COLLECTION
    # =========================================================================

    @property
    def reviews(self) -> Collection:
        """Get the reviews collection."""
        if self._reviews is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._reviews

    def create_review(self, review_data: dict) -> str:
        """
        Create a new review record.

        Args:
            review_data: Review document containing:
                - employee_id: ObjectId of the employee
                - employee_name: Name for quick reference
                - template: Template name used
                - file_path: Path to markdown file
                - pdf_path: Path to PDF file (optional)
                - review_period: Period being reviewed
                - generated_by: Who/what generated it

        Returns:
            Inserted review ID as string.
        """
        review_data["generated_at"] = datetime.utcnow()
        review_data["status"] = review_data.get("status", "draft")
        result = self._reviews.insert_one(review_data)
        return str(result.inserted_id)

    def get_review(self, review_id: str) -> Optional[dict]:
        """Get a review by ID."""
        try:
            review = self._reviews.find_one({"_id": ObjectId(review_id)})
            if review:
                review["_id"] = str(review["_id"])
                if "employee_id" in review:
                    review["employee_id"] = str(review["employee_id"])
            return review
        except Exception:
            return None

    def get_reviews_by_employee(self, employee_id: str) -> list[dict]:
        """Get all reviews for an employee by their ID."""
        try:
            reviews = list(self._reviews.find(
                {"employee_id": ObjectId(employee_id)}
            ).sort("generated_at", DESCENDING))
            for r in reviews:
                r["_id"] = str(r["_id"])
                r["employee_id"] = str(r["employee_id"])
            return reviews
        except Exception:
            return []

    def get_all_reviews(self, limit: int = 100) -> list[dict]:
        """Get all reviews with optional limit."""
        reviews = list(self._reviews.find().sort("generated_at", DESCENDING).limit(limit))
        for r in reviews:
            r["_id"] = str(r["_id"])
            if "employee_id" in r:
                r["employee_id"] = str(r["employee_id"])
        return reviews

    def update_review_status(self, review_id: str, status: str) -> bool:
        """Update review status (draft, pending_approval, approved, archived)."""
        try:
            result = self._reviews.update_one(
                {"_id": ObjectId(review_id)},
                {"$set": {"status": status, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception:
            return False

    def delete_review(self, review_id: str) -> bool:
        """Delete a review."""
        try:
            result = self._reviews.delete_one({"_id": ObjectId(review_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    # =========================================================================
    # BULK OPERATIONS
    # =========================================================================

    def bulk_insert_employees(self, employees: list[dict]) -> dict:
        """
        Insert multiple employees at once.

        Args:
            employees: List of employee documents.

        Returns:
            Dict with 'inserted' count and 'errors' list.
        """
        results = {"inserted": 0, "skipped": 0, "errors": []}

        for emp in employees:
            name = emp.get("name", "")
            if not name:
                results["errors"].append({"data": emp, "error": "Missing name field"})
                continue

            if self.employee_exists(name):
                results["skipped"] += 1
                results["errors"].append({"name": name, "error": "Employee already exists"})
                continue

            try:
                self.insert_employee(emp)
                results["inserted"] += 1
            except Exception as e:
                results["errors"].append({"name": name, "error": str(e)})

        return results

    # =========================================================================
    # AUDIT LOGS COLLECTION
    # =========================================================================

    @property
    def audit_logs(self) -> Collection:
        """Get the audit logs collection."""
        if self._audit_logs is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._audit_logs

    def log_action(
        self,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
        user: str = "system",
    ) -> str:
        """
        Log an action to the audit log.

        Args:
            action: Action type (create, read, update, delete, generate)
            resource_type: Type of resource (employee, review, template)
            resource_id: ID of the affected resource
            details: Additional details about the action
            user: Who performed the action

        Returns:
            Inserted log ID as string.
        """
        log_entry = {
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "user": user,
            "timestamp": datetime.utcnow(),
        }
        result = self._audit_logs.insert_one(log_entry)
        return str(result.inserted_id)

    def get_audit_logs(
        self,
        limit: int = 100,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
    ) -> list[dict]:
        """
        Get audit logs with optional filtering.

        Args:
            limit: Maximum number of logs to return.
            resource_type: Filter by resource type.
            action: Filter by action type.

        Returns:
            List of audit log entries.
        """
        query = {}
        if resource_type:
            query["resource_type"] = resource_type
        if action:
            query["action"] = action

        logs = list(
            self._audit_logs.find(query)
            .sort("timestamp", DESCENDING)
            .limit(limit)
        )
        for log in logs:
            log["_id"] = str(log["_id"])
        return logs

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_statistics(self) -> dict:
        """
        Get various statistics about the database.

        Returns:
            Dict containing counts and aggregated stats.
        """
        stats = {
            "employees": {
                "total": self._collection.count_documents({}),
                "by_department": {},
                "by_level": {},
            },
            "reviews": {
                "total": self._reviews.count_documents({}),
                "by_status": {},
                "by_template": {},
            },
            "templates": {
                "total": self._templates.count_documents({}),
                "active": self._templates.count_documents({"active": True}),
            },
            "audit_logs": {
                "total": self._audit_logs.count_documents({}),
            },
        }

        # Employees by department
        pipeline = [
            {"$group": {"_id": "$department", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        for doc in self._collection.aggregate(pipeline):
            dept = doc["_id"] or "Unknown"
            stats["employees"]["by_department"][dept] = doc["count"]

        # Employees by level
        pipeline = [
            {"$group": {"_id": "$level", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        for doc in self._collection.aggregate(pipeline):
            level = doc["_id"] or "Unknown"
            stats["employees"]["by_level"][level] = doc["count"]

        # Reviews by status
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        ]
        for doc in self._reviews.aggregate(pipeline):
            status = doc["_id"] or "draft"
            stats["reviews"]["by_status"][status] = doc["count"]

        # Reviews by template
        pipeline = [
            {"$group": {"_id": "$template", "count": {"$sum": 1}}},
        ]
        for doc in self._reviews.aggregate(pipeline):
            template = doc["_id"] or "Unknown"
            stats["reviews"]["by_template"][template] = doc["count"]

        return stats

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
