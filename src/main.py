#!/usr/bin/env python3

"""Main module my cool API 😉."""

import os

from bson.objectid import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

DATABASE_NAME = "Notebooks"
COLLECTION_NAME = "User Notebooks"


load_dotenv()
connection_string = os.getenv("MONGO_CONNECTION_STRING")

client: MongoClient = MongoClient(connection_string, server_api=ServerApi("1"))
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]


description = """
Jupyter Notebook Backend API helps you do awesome notebooks. 🚀
"""

app = FastAPI(
    title="Jupyter Backend API",
    description=description,
    version="0.0.1",
)


def document_to_dict(document) -> dict:
    """Convert a MongoDB document to a Python dict, converting '_id' to string."""
    document["_id"] = str(document["_id"])
    return document


@app.get("/")
def read_root() -> dict:
    """Return a simple message."""
    return {"👋 Hello": "Jupyter clone!"}


@app.get("/ping-db")
def ping() -> dict:
    """Ping the database."""
    try:
        response: dict = client.admin.command("ping")
        return {"Ping Database": f"🟢 Success, database is available {response}"}
    except Exception as e:
        return {"Error": e}


@app.get("/notebooks")
def get_notebooks() -> dict:
    """Get all documents in the collection."""
    try:
        cursor = collection.find()
        documents = [document_to_dict(document) for document in cursor]
        return {"documents": documents}
    except Exception as e:
        return {"error": str(e)}


@app.get("/notebooks/{user_email}")
def get_user_notebooks(user_email: str) -> dict:
    """Get names of all documents belonging to a specific user.

    Args:
        user_email (str): The email of the user whose documents to retrieve.
    """
    try:
        cursor = collection.find({"user": user_email})
        document_names = [doc["filename"] for doc in cursor]
        return {"document_names": document_names}
    except Exception as e:
        return {"error": str(e)}


@app.get("/notebook/{document_id}")
def get_notebook(document_id: str) -> dict:
    """Get a specific document by its id.

    Args:
        document_id (str): The id of the document to retrieve.
    """
    try:
        oid: ObjectId = ObjectId(document_id)
        if document := collection.find_one({"_id": oid}):
            return {"document": document_to_dict(document)}
        else:
            return {"error": "No document found with this id."}
    except Exception as e:
        return {"error": str(e)}


@app.delete("/notebook/{document_id}")
def delete_notebook(document_id: str) -> dict:
    """Delete a specific document by its id.

    Args:
        document_id (str): The id of the document to delete.
    """
    try:
        oid: ObjectId = ObjectId(document_id)
        result = collection.delete_one({"_id": oid})
        if result.deleted_count:
            return {"success": f"Document with id {document_id} deleted successfully."}
        else:
            return {"error": "No document found with this id to delete."}
    except Exception as e:
        return {"error": str(e)}
