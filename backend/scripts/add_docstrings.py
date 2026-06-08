"""One-off script to insert missing function/method docstrings in the backend app."""

from __future__ import annotations

import ast
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]

DOCSTRINGS: dict[str, dict[str, str]] = {
    "app/main.py": {
        "lifespan": "Initialize the database and log the configured AI provider on startup.",
        "create_app": "Build and configure the FastAPI application instance.",
        "_register_middleware": "Attach CORS and OAuth session middleware.",
        "_register_exception_handlers": "Map domain exceptions to HTTP error responses.",
        "_register_routes": "Mount API routers under the /api prefix.",
        "unauthorized_handler": "Return HTTP 401 for authentication failures.",
        "forbidden_handler": "Return HTTP 403 for authorization failures.",
        "not_found_handler": "Return HTTP 404 for missing resources.",
        "bad_request_handler": "Return HTTP 400 for invalid client input.",
        "service_unavailable_handler": "Return HTTP 503 when a dependency is unavailable.",
        "generation_failed_handler": "Return HTTP 502 when architecture generation fails.",
        "ai_client_handler": "Return HTTP 503 when the AI provider call fails.",
    },
    "app/core/dependencies.py": {
        "get_jwt_service": "Provide a JWT encoder/decoder for session cookies.",
        "get_ai_client": "Provide the configured AI client (OpenAI or static).",
        "get_auth_service": "Provide an AuthService bound to the request database session.",
        "get_project_service": "Provide a ProjectService bound to the request database session.",
        "get_generation_service": "Provide a GenerationService with AI client and database session.",
        "get_catalog_service": "Provide static wizard catalog data.",
        "get_current_user": "Resolve and return the authenticated user from the session cookie.",
    },
    "app/core/database.py": {
        "_engine_kwargs": "Return SQLAlchemy engine options appropriate for the database URL.",
        "get_db": "Yield a request-scoped database session and close it afterward.",
        "initialize": "Create tables and apply incremental schema migrations.",
        "_apply_migrations": "Add new columns and drop legacy columns on existing databases.",
        "_ensure_column": "Run DDL to add a column when it is missing from a table.",
        "_drop_column_if_exists": "Remove a legacy column from a table when present.",
        "init_db": "Initialize database schema at application startup.",
    },
    "app/core/logging.py": {
        "__init__": "Wire the underlying Python logger instance.",
        "log_step": "Log a generation pipeline step with project and request context.",
        "log_started": "Log the start of an AI client operation.",
        "log_completed": "Log successful completion of an AI client operation.",
        "log_failed": "Log a failed AI client operation with reason.",
    },
    "app/api/controllers/project_controller.py": {
        "__init__": "Wire project, generation, and catalog services.",
        "list_project_types": "Return supported project type options for the wizard.",
        "create_project": "Persist a new project owned by the authenticated user.",
        "generate_project": "Run AI architecture generation for an owned project.",
    },
    "app/api/controllers/auth_controller.py": {
        "__init__": "Wire the authentication service.",
        "google_login": "Start the Google OAuth authorization redirect.",
        "google_callback": "Complete Google OAuth and set the session cookie.",
        "current_user": "Return the authenticated user's public profile.",
        "logout": "Clear the session cookie.",
        "_session_cookie": "Build cookie kwargs for a new session token.",
        "_clear_session_cookie": "Build cookie kwargs that expire the session cookie.",
    },
    "app/api/controllers/health_controller.py": {
        "check": "Return service health and AI configuration status.",
    },
    "app/api/routes/project_routes.py": {
        "_controller": "Build a ProjectController from injected services.",
        "list_project_types": "HTTP handler for GET /project-types.",
        "create_project": "HTTP handler for POST /projects.",
        "generate_project": "HTTP handler for POST /projects/{project_id}/generate.",
    },
    "app/api/routes/auth_routes.py": {
        "_controller": "Build an AuthController from the auth service.",
        "google_login": "HTTP handler for GET /auth/google.",
        "google_callback": "HTTP handler for GET /auth/google/callback.",
        "auth_me": "HTTP handler for GET /auth/me.",
        "logout": "HTTP handler for POST /auth/logout.",
    },
    "app/api/routes/health_routes.py": {
        "_controller": "Build a HealthController instance.",
        "health": "HTTP handler for GET /health.",
    },
    "app/services/project_service.py": {
        "__init__": "Wire the project repository.",
        "create": "Create a project for the given user and commit it.",
        "get_owned_project": "Load a project and verify the requesting user owns it.",
    },
    "app/services/catalog_service.py": {
        "list_project_types": "Return the static list of wizard project types.",
    },
    "app/services/auth_service.py": {
        "__init__": "Wire user repository, JWT service, and OAuth client.",
        "oauth_client": "Expose the configured Google OAuth client.",
        "ensure_oauth_configured": "Raise when Google OAuth credentials are missing.",
        "start_google_login": "Redirect the browser to Google's authorization endpoint.",
        "complete_google_login": "Exchange the OAuth code, upsert the user, and issue a session token.",
        "_parse_google_profile": "Validate Google userinfo and map it to a profile dataclass.",
        "_upsert_user": "Create or update a user record from a Google profile.",
    },
    "app/services/cost_estimator_service.py": {
        "estimate": "Compute monthly cost ranges for each cloud provider.",
        "_estimate_for_provider": "Calculate the cost band for a single provider.",
        "_apply_feature_bands": "Add optional feature cost bands to a baseline estimate.",
        "_apply_production_band": "Add production-stage overhead to a cost band.",
        "_apply_user_multiplier": "Scale cost bounds by expected user count.",
        "_build_notes": "Build human-readable notes explaining the estimate.",
    },
    "app/services/generation_storage_service.py": {
        "__init__": "Wire the object storage client.",
        "build_request_payload": "Build the JSON artifact saved before calling the AI.",
        "build_response_payload": "Build the JSON artifact saved after AI validation.",
        "save_request": "Persist a generation request artifact to object storage.",
        "save_response": "Persist a generation response artifact to object storage.",
        "resolve_model_name": "Return the AI model name or 'static' for canned responses.",
        "_object_key": "Build the storage key for a generation artifact file.",
        "_model_parameters": "Capture prompt/model settings stored with each request.",
        "_original_user_input": "Snapshot wizard inputs included in the request artifact.",
        "_utc_iso": "Return the current UTC timestamp in ISO format.",
    },
    "app/repositories/base.py": {
        "__init__": "Store the SQLAlchemy session used by repository methods.",
        "commit": "Commit the current transaction.",
        "flush": "Flush pending changes without committing.",
        "refresh": "Reload an ORM instance from the database.",
    },
    "app/repositories/project_repository.py": {
        "__init__": "Wire the SQLAlchemy session.",
        "find_by_id": "Load a project by primary key.",
        "create": "Insert a new project and its requirement answers.",
        "clear_generated_content": "Remove previously generated components, costs, risks, and recommendations.",
        "persist_architecture": "Replace generated architecture data on a project.",
        "_add_components": "Attach mapped components and cloud mappings to a project.",
        "_add_costs": "Attach provider cost estimates to a project.",
    },
    "app/repositories/user_repository.py": {
        "__init__": "Wire the SQLAlchemy session.",
        "find_by_id": "Load a user by primary key.",
        "find_by_google_sub": "Load a user by Google subject id.",
        "create": "Insert a new user record.",
        "update_profile": "Update a user's profile fields from OAuth data.",
    },
    "app/repositories/generation_request_repository.py": {
        "__init__": "Wire the SQLAlchemy session.",
        "create_pending": "Insert a pending architecture generation request for a project.",
        "save_prompt_path": "Record the object storage path of the saved prompt artifact.",
        "save_output_path": "Record the object storage path of the saved response artifact.",
        "mark_completed": "Mark a generation request as completed.",
        "mark_failed": "Mark a generation request as failed.",
    },
    "app/clients/storage_client.py": {
        "write_json": "Persist JSON at the given object key.",
        "read_json": "Load JSON previously stored at the given key.",
        "_bucket_ref": "Lazily initialize and return the GCS bucket reference.",
        "create": "Instantiate the configured storage client implementation.",
    },
    "app/clients/ai_client.py": {
        "generate": "Return raw JSON text from the AI provider.",
        "create": "Select static or OpenAI client based on runtime settings.",
    },
    "app/clients/google_oauth_client.py": {
        "__init__": "Register the Google OAuth client with Authlib.",
        "authorize_redirect": "Redirect the user to Google's OAuth consent screen.",
        "authorize_access_token": "Exchange the authorization code for tokens.",
        "fetch_userinfo": "Fetch Google profile data for the authenticated user.",
    },
    "app/clients/static_payload.py": {
        "_option_detail": "Build one implementation option detail object.",
        "_na_option": "Build a not-applicable implementation option placeholder.",
        "_implementation_options": "Build the full implementation options block for a component.",
    },
    "app/config/settings.py": {
        "cors_origins_list": "Parse CORS origins from a comma-separated env string.",
        "oauth_configured": "Return True when Google OAuth client credentials are set.",
        "strip_secret_whitespace": "Strip trailing whitespace from secret env values.",
    },
    "app/services/prompt_builder_service.py": {
        "build": "Construct the full LLM prompt from a project's wizard answers.",
        "_build_answers_dict": "Map requirement answer fields to a boolean dict.",
        "_format_requirements": "Format requirement toggles as bullet lines for the prompt.",
        "_assemble_prompt": "Combine project metadata and requirements into the final prompt.",
        "_stage_guidance": "Return MVP or Production guidance text for the prompt.",
        "_yes_no": "Format a boolean requirement as Yes or No.",
    },
    "app/services/cloud_defaults_service.py": {
        "default_cloud_options_for_type": "Return default cloud services for a component type.",
        "normalize_cloud_options": "Fill missing provider lists and normalize aliases.",
        "_options_for_provider": "Extract cloud options for one provider from AI output.",
    },
    "app/services/component_mapper_service.py": {
        "map_payload": "Map validated AI JSON to components, summary, and flow steps.",
        "feature_flags_from_components": "Derive cost-estimation feature flags from component keys.",
        "_map_components": "Map each AI component object to a MappedComponent.",
        "_map_single_component": "Map one AI component dict to a MappedComponent.",
        "_resolve_component_type": "Normalize and validate a component type string.",
        "_extract_cloud_options": "Normalize per-provider cloud option lists.",
        "_extract_implementation_options": "Normalize implementation option metadata.",
        "infer_component_key": "Derive a stable internal key for a component.",
        "_unique_slug": "Generate a unique slug key when hints do not match.",
        "_slugify": "Convert a display name into a lowercase slug.",
    },
    "app/services/architecture_guardrail_service.py": {
        "from_project": "Build guardrail context from a project's stage and answers.",
        "apply": "Apply cost-aware guardrails to validated AI component output.",
        "_apply_component_tag_guardrails": "Downgrade analytics to optional when dashboards are off.",
        "_apply_cloud_option_guardrails": "Swap expensive cloud services for MVP alternatives.",
        "_normalize_provider_options": "Replace expensive options with cheaper alternatives.",
        "_is_expensive_option": "Return True when a cloud option matches expensive patterns.",
        "_prefer_external_ai_implementation": "Recommend external AI APIs for small MVP workloads.",
    },
    "app/utils/jwt.py": {
        "__init__": "Load JWT signing settings.",
        "create_access_token": "Issue a signed session token for a user id.",
        "decode_access_token": "Validate a session token and return the user id, or None.",
    },
    "app/models/_helpers.py": {
        "_uuid": "Generate a new UUID string for primary keys.",
        "_now": "Return the current UTC datetime for ORM defaults.",
    },
    "app/schemas/project.py": {
        "dedupe_types": "Remove duplicate project types while preserving order.",
        "validate_description_length": "Reject descriptions longer than the configured limit.",
    },
    "app/services/generation_service.py": {
        "request_id": "Return the generation request id for this run.",
        "project_id": "Return the project id for this run.",
        "__init__": "Wire AI, validation, mapping, cost, storage, and repository dependencies.",
        "generate": "Run the full generation pipeline and return the updated project.",
        "_start_generation": "Create a pending generation request and initialize run state.",
        "_execute_generation_pipeline": "Run prompt build, AI call, validation, mapping, and persistence.",
        "_persist_request_artifact": "Save the prompt artifact and record its storage path.",
        "_call_ai_step": "Invoke the AI client and capture timing and errors.",
        "_validate_ai_step": "Validate AI output, apply guardrails, and record parse results.",
        "_record_successful_response": "Persist the response artifact after successful validation.",
        "_process_validated_output": "Map components, estimate costs, and persist the architecture.",
        "_record_unexpected_error": "Append unexpected errors to the response artifact when possible.",
        "_save_run_response": "Write the current run state to the response artifact.",
        "_fail_generation": "Mark the generation request failed and log the reason.",
        "_finish_generation": "Commit changes and reload the project from the database.",
        "_save_generation_response": "Build and store the response JSON artifact.",
        "_create_request": "Insert a pending ArchitectureGenerationRequest row.",
        "_build_prompt": "Build and log the LLM prompt for the project.",
        "_call_ai": "Call the AI client and log response size.",
        "_validate_response": "Validate raw AI JSON and apply architecture guardrails.",
        "_map_payload": "Map validated AI JSON to internal component models.",
        "_estimate_costs": "Compute provider cost estimates from mapped components.",
        "_persist_document": "Save components, costs, diagrams, and summary on the project.",
        "_complete_request": "Mark the generation request as completed.",
        "_handle_failure": "Log failure, mark the request failed, and commit.",
        "_GenerationRun": "Mutable state tracked while a single generation request runs.",
    },
    "app/validators/ai_response_validator.py": {
        "__init__": "Wire cloud defaults used to normalize provider options.",
        "validate": "Parse, normalize, and validate raw AI JSON architecture output.",
        "_parse_json": "Parse extracted JSON text into a dict.",
        "_extract_json": "Strip markdown fences and isolate the JSON object from AI text.",
        "_validate_top_level": "Ensure required top-level fields are present.",
        "_validate_components": "Validate each component in the AI response.",
        "_validate_component": "Validate and normalize a single component object.",
        "_normalize_implementation_options": "Validate recommended model and option details.",
        "_normalize_option_detail": "Normalize one implementation option detail object.",
        "_normalize_string_list": "Normalize a list field to non-empty strings.",
        "_validate_architecture": "Validate architecture summary and flow fields.",
        "_validate_diagrams": "Validate required high-level and system-flow diagrams.",
        "_validate_diagram": "Validate one diagram's title, nodes, and edges.",
        "_validate_nodes": "Validate diagram nodes and collect unique ids.",
        "_validate_node": "Validate and normalize a single diagram node.",
        "_validate_edges": "Validate diagram edges against known node ids.",
        "_validate_edge": "Validate and normalize a single diagram edge.",
    },
}


def _indent_of_line(line: str) -> str:
    return line[: len(line) - len(line.lstrip(" "))]


def _insert_after_signature(lines: list[str], node: ast.AST, doc: str) -> None:
    start = node.lineno - 1
    end = start
    while end < len(lines) and ":" not in lines[end]:
        end += 1
    indent = _indent_of_line(lines[start]) + "    "
    if isinstance(node, ast.ClassDef):
        indent = _indent_of_line(lines[start]) + "    "
    doc_line = f'{indent}"""{doc}"""\n'
    lines.insert(end + 1, doc_line)


def process_file(rel_path: str) -> bool:
    mapping = DOCSTRINGS.get(rel_path)
    if not mapping:
        return False

    path = BACKEND / Path(rel_path)
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    targets: list[tuple[ast.AST, str]] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if ast.get_docstring(node):
            continue
        doc = mapping.get(node.name)
        if doc:
            targets.append((node, doc))

    if not targets:
        return False

    lines = source.splitlines(keepends=True)
    for node, doc in sorted(targets, key=lambda item: item[0].lineno, reverse=True):
        _insert_after_signature(lines, node, doc)

    path.write_text("".join(lines), encoding="utf-8")
    print(f"updated {rel_path} ({len(targets)} docstrings)")
    return True


def main() -> int:
    updated = sum(1 for rel_path in DOCSTRINGS if process_file(rel_path))
    print(f"Done. Updated {updated} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
