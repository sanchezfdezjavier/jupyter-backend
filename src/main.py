#!/usr/bin/env python3

"""Main module for my cool Jupyter Notebooks API 😉."""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from bson.objectid import ObjectId
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from IPython.core.interactiveshell import InteractiveShell
from pydantic import BaseModel
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from contextlib import redirect_stdout
import io

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

# FIXME: Not super secure 😆
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


class ExecutionContextManager:
    """Manage execution contexts for notebooks."""

    def __init__(self):
        """Create a new execution context manager."""
        self.contexts = {}

    def create_context(self, notebook_id: str) -> InteractiveShell:
        """Create a new execution context for a notebook.

        Args:
            notebook_id (str): The id of the notebook to create a context for.

        Returns:
            InteractiveShell: The execution context for the notebook.
        """
        shell = InteractiveShell()
        self.contexts[notebook_id] = shell
        return shell

    def get_context(self, notebook_id: str) -> Optional[InteractiveShell]:
        """Get the execution context for a notebook.

        Args:
            notebook_id (str): The id of the notebook to get the context for.

        Returns:
            InteractiveShell: The execution context for the notebook.
        """
        return self.contexts.get(notebook_id)

    def remove_context(self, notebook_id: str) -> None:
        """Remove the execution context for a notebook.

        Args:
            notebook_id (str): The id of the notebook to remove the context for.
        """
        self.contexts.pop(notebook_id, None)


def document_to_dict(document) -> dict:
    """Convert a MongoDB document to a Python dict, converting '_id' to string."""
    document["_id"] = str(document["_id"])
    return document


@app.get("/")
def connectivity_test() -> dict:
    """Return a simple message.

    Returns:
        dict: A simple message.
    """
    return {"👋 Hello": "I'm the Jupyter API!"}


@app.get("/ping-db")
def ping_db() -> dict:
    """Ping the database.

    Returns:
        dict: A simple message.
    """
    try:
        response: dict = client.admin.command("ping")
        return {"Ping Database": f"🟢 Success, database is available {response}"}
    except Exception as e:
        return {"Error": e}


@app.get("/notebooks")
def get_notebooks() -> dict:
    """Get all documents in the collection.

    Returns:
        dict: A list of all documents in the collection.
    """
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

    Returns:
        dict: A list of all documents belonging to the user.
    """
    try:
        cursor = collection.find({"user": user_email})
        user_documents = [{"filename": doc["filename"], "_id": str(doc["_id"])} for doc in cursor]
        return {"user_documents": user_documents}
    except Exception as e:
        return {"error": str(e)}


@app.get("/notebook/{document_id}")
def get_notebook(document_id: str) -> dict:
    """Get a specific document by its id.

    Args:
        document_id (str): The id of the document to retrieve.

    Returns:
        dict: The document with the given id.
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

    Returns:
        dict: A message indicating whether the document was deleted successfully.
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


class Document(BaseModel):
    """Create notebook POST request body model."""

    filename: str
    user: str


@app.post("/notebook")
def create_notebook(document: Document) -> dict:
    """Create a new document.

    Args:
        document (Document): The document to create.

    Returns:
        dict: A message indicating whether the document was created successfully.
    """
    filename = document.filename
    user = document.user

    default_notebook_structure = {
        "cells": [],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.8.10",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    try:
        new_document = {
            "notebook": default_notebook_structure,
            "user": user,
            "filename": filename,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        result = collection.insert_one(new_document)
        return {"success": f"Document with id {result.inserted_id} created successfully."}
    except Exception as e:
        return {"error": str(e)}


class Cell(BaseModel):
    """Create cell model."""

    cell_type: str
    source: List[str]
    metadata: Optional[Dict[str, Any]] = {}
    execution_count: Optional[int] = None
    outputs: Optional[List[Dict[str, Any]]] = []


@app.delete("/notebook/{notebook_id}/cell/{cell_id}")
def delete_cell(notebook_id, cell_id) -> dict:
    """Delete a specific cell by its id from a notebook.

    Args:
        notebook_id (str): The id of the notebook containing the cell.
        cell_id (int): The id of the cell to delete.

    Returns:
        dict: A message indicating whether the cell was deleted successfully.
    """
    try:
        oid: ObjectId = ObjectId(notebook_id)
        result = collection.update_one(
            {"_id": oid},
            {"$pull": {"notebook.cells": {"id": cell_id}}, "$set": {"updated_at": datetime.now()}},  # noqa E501
        )
        if result.modified_count:
            return {"success": f"Cell with id {cell_id} deleted successfully from notebook {notebook_id}."}  # noqa E501
        else:
            return {"error": "No cell found with this id to delete."}
    except Exception as e:
        return {"error": str(e)}


context_manager = ExecutionContextManager()


class ExecuteCodeBody(BaseModel):
    """Execute code request body model."""

    source: str


@app.post("/notebook/{notebook_id}/cell/{cell_id}/execute_and_update")
def execute_and_update_code(notebook_id: str, cell_id: str, body: dict) -> dict:
    """Execute code and update cell.

    Args:
        notebook_id (str): The id of the notebook containing the cell.
        cell_id (str): The id of the cell to add/update.
        body (dict): The request body containing the code to execute.

    Returns:
        dict: The output of the code.
    """
    code = body.get("source", "")
    try:
        shell = context_manager.get_context(notebook_id) or context_manager.create_context(notebook_id)  # noqa E501

        stout = io.StringIO()
        with redirect_stdout(stout):
            result = shell.run_cell(code).result

        printed_output = stout.getvalue()
        cell = {"id": cell_id, "source": code, "outputs": str(printed_output)}

        document = collection.find_one({"_id": ObjectId(notebook_id), "notebook.cells.id": cell_id})  # noqa E501
        if document is None:
            # Cell doesn't exist, push new cell
            update_result = collection.update_one(
                {"_id": ObjectId(notebook_id)}, {"$push": {"notebook.cells": cell}}
            )  # noqa E501
            if update_result.matched_count < 1:
                return {"output": None, "error": "Failed to insert cell"}
        else:
            # Cell exists, update it
            update_result = collection.update_one(
                {"_id": ObjectId(notebook_id), "notebook.cells.id": cell_id},
                {
                    "$set": {
                        "notebook.cells.$.source": code,
                        "notebook.cells.$.outputs": str(printed_output),
                        "updated_at": datetime.now(),
                    }
                },
            )
            if update_result.matched_count < 1:
                return {"output": None, "error": "Failed to update cell"}

        return {"output": str(printed_output), "error": None}
    except Exception as e:
        return {"output": None, "error": str(e)}
