"""List global_usage_models subcollections in Firestore."""

from __future__ import annotations

from app.clients.firestore_client import get_firestore_client
from app.config.params import (
    FIRESTORE_GLOBAL_USAGE_MODELS_SUBCOLLECTION,
    FIRESTORE_PROJECTS_COLLECTION,
)


def main() -> int:
    client = get_firestore_client()
    print(f"Firestore project: {client.project}")

    projects = list(client.collection(FIRESTORE_PROJECTS_COLLECTION).limit(10).stream())
    print(f"Projects found: {len(projects)}")
    if not projects:
        print("No projects in Firestore.")
        return 0

    for project in projects:
        models = list(
            project.reference.collection(FIRESTORE_GLOBAL_USAGE_MODELS_SUBCOLLECTION).stream()
        )
        print(f"\nprojects/{project.id}/global_usage_models -> {len(models)} document(s)")
        for model in models:
            data = model.to_dict() or {}
            print(f"  {model.id}")
            print(f"    selection_id: {data.get('selection_id')}")
            print(f"    model: {data.get('model')}")
            print(f"    created_at: {data.get('created_at')}")
            print(f"    prompt: {'yes' if data.get('prompt') else 'no'}")
            print(f"    raw_response: {'yes' if data.get('raw_response') else 'no'}")
            print(f"    model_output: {'yes' if data.get('model_output') else 'no'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
