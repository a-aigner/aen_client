"""
manager.py – Core client for the Aeneis API v2 (aen_client)

Features
- Cookie-based session auth: login via Basic Auth to /user/login, then reuse Set-Cookie.
- Clean wrappers for objects, search, queries, files, transactions, locale, version view, and upload dir.
- Centralized error handling mapped to custom exceptions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests
from requests.auth import HTTPBasicAuth

from .exceptions import (
    AuthenticationError,
    ConflictError,
    AenClientError,
    NotFoundError,
    PermissionDenied,
    ServerError,
    TransactionError,
    ValidationError,
)
from .types import AenFile, AenObject, QueryResult, View
from .utils import build_url, merge_params


class AenClient:
    """
    Client for the Aeneis API v2.

    Auth flow:
        login() -> GET /user/login using Basic Auth
        (server sets a session cookie)
        subsequent requests use cookie (no Basic Auth)
        logout() -> GET /user/logout and clear local cookies
    """

    def __init__(
        self,
        base_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        service_id: Optional[str] = None,
        *,
        timeout: int = 30,
        user_agent: str = "aen-client/0.1",
        raise_for_status: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.service_id = service_id
        self.timeout = timeout
        self.raise_for_status = raise_for_status

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": user_agent,
            }
        )

    # --------------------------------------------------------------------- #
    # Auth lifecycle
    # --------------------------------------------------------------------- #
    def login(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        *,
        service_id: Optional[str] = None,
    ) -> None:
        """
        Establish a cookie-backed session against /user/login.

        On success, requests.Session stores the Set-Cookie automatically.
        """
        user = username or self.username
        pwd = password or self.password
        if not (user and pwd):
            raise AuthenticationError("username and password are required for login")

        params: Dict[str, Any] = {}
        sid = service_id if service_id is not None else self.service_id
        if sid:
            params["service_id"] = sid

        url = build_url(self.base_url, "/user/login")
        resp = self.session.get(
            url,
            params=params or None,
            auth=HTTPBasicAuth(user, pwd),
            timeout=self.timeout,
        )

        if resp.status_code != 200:
            self._raise_api_error(resp)

        # After successful login, we rely solely on the session cookie.
        self.session.auth = None

    def logout(self) -> None:
        """Terminate server session and clear local cookies."""
        url = build_url(self.base_url, "/user/logout")
        resp = self.session.get(url, timeout=self.timeout)
        if resp.status_code != 200:
            self._raise_api_error(resp)
        self.session.cookies.clear()

    # --------------------------------------------------------------------- #
    # Objects (single)
    # --------------------------------------------------------------------- #
    def get_object(self, object_id: str, *, view: Optional[View] = "detailed") -> AenObject:
        url = build_url(self.base_url, f"/object/{object_id}")
        resp = self.session.get(url, params={"view": view} if view else None, timeout=self.timeout)
        return self._json_or_error(resp)

    def create_object(
        self,
        *,
        category_id: str,
        parent_id: str,
        attribute_name: str,
        properties: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        url = build_url(self.base_url, "/object")
        params = {
            "category_id": category_id,
            "parent_id": parent_id,
            "attribute_name": attribute_name,
        }
        body = properties or []
        resp = self.session.post(url, params=params, json=body, timeout=self.timeout)
        return self._json_or_error(resp)

    def update_object(self, *, object_id: str, properties: List[Dict[str, Any]]) -> Dict[str, Any]:
        url = build_url(self.base_url, "/object")
        payload = {"id": object_id, "properties": properties}
        resp = self.session.put(url, json=payload, timeout=self.timeout)
        return self._json_or_error(resp)

    def delete_object(self, object_id: str) -> None:
        url = build_url(self.base_url, f"/object/{object_id}")
        resp = self.session.delete(url, timeout=self.timeout)
        if resp.status_code != 200:
            self._raise_api_error(resp)

    # --------------------------------------------------------------------- #
    # Objects (bulk)
    # --------------------------------------------------------------------- #
    def get_objects(self, object_ids: List[str], *, view: Optional[View] = "detailed") -> Dict[str, Any]:
        url = build_url(self.base_url, "/objects")
        params: Dict[str, Any] = {"object_id": object_ids}
        if view:
            params["view"] = view
        resp = self.session.get(url, params=params, timeout=self.timeout)
        return self._json_or_error(resp)

    def create_objects(self, objects: List[Dict[str, Any]]) -> Dict[str, Any]:
        url = build_url(self.base_url, "/objects")
        resp = self.session.post(url, json=objects, timeout=self.timeout)
        return self._json_or_error(resp)

    def update_objects(self, objects: List[Dict[str, Any]]) -> None:
        url = build_url(self.base_url, "/objects")
        resp = self.session.put(url, json={"objects": objects}, timeout=self.timeout)
        if resp.status_code != 200:
            self._raise_api_error(resp)

    def delete_objects(self, object_ids: List[str]) -> None:
        url = build_url(self.base_url, "/objects")
        resp = self.session.delete(url, params={"object_id": object_ids}, timeout=self.timeout)
        if resp.status_code != 200:
            self._raise_api_error(resp)

    # --------------------------------------------------------------------- #
    # Search
    # --------------------------------------------------------------------- #
    def search(
        self,
        q: str,
        *,
        view: Optional[View] = None,
        attribute_name: Optional[List[str]] = None,
        category_id: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        url = build_url(self.base_url, "/search")
        params = merge_params(
            {"q": q},
            {"view": view},
            {"attribute_name": attribute_name},
            {"category_id": category_id},
            {"limit": limit},
        )
        resp = self.session.get(url, params=params, timeout=self.timeout)
        return self._json_or_error(resp)

    def search_by_component(
        self,
        component_id: str,
        object_id: List[str],
        *,
        view: Optional[View] = "detailed",
    ) -> List[Dict[str, Any]]:
        url = build_url(self.base_url, f"/search/{component_id}")
        params = {"object_id": object_id, "view": view}
        resp = self.session.get(url, params=params, timeout=self.timeout)
        return self._json_or_error(resp)

    # --------------------------------------------------------------------- #
    # Queries
    # --------------------------------------------------------------------- #
    def get_object_query_result(
        self, object_id: str, query_id: str, *, view: Optional[View] = "detailed"
    ) -> QueryResult:
        url = build_url(self.base_url, f"/object/{object_id}/query/{query_id}")
        resp = self.session.get(url, params={"view": view} if view else None, timeout=self.timeout)
        return self._json_or_error(resp)

    def get_objects_query_result(
        self, query_id: str, object_ids: List[str], *, view: Optional[View] = "detailed"
    ) -> Dict[str, Any]:
        url = build_url(self.base_url, f"/objects/query/{query_id}")
        params = {"object_id": object_ids, "view": view}
        resp = self.session.get(url, params=params, timeout=self.timeout)
        return self._json_or_error(resp)

    # --------------------------------------------------------------------- #
    # Files on objects
    # --------------------------------------------------------------------- #
    def list_files(self, object_id: str) -> List[AenFile]:
        url = build_url(self.base_url, f"/object/{object_id}/file/")
        try:
            resp = self.session.get(url, timeout=self.timeout)
            return self._json_or_error(resp)
        except AenClientError as e:
            # Some objects don´t support file operations
            if resp.status_code == 405:
                return []

    def get_file(
        self,
        object_id: str,
        filename: str,
        *,
        attribute_name: Optional[str] = None,
        position: Optional[int] = None,
    ) -> AenFile:
        url = build_url(self.base_url, f"/object/{object_id}/file/{filename}")
        params = merge_params({"attribute_name": attribute_name}, {"position": position})
        resp = self.session.get(url, params=params, timeout=self.timeout)
        return self._json_or_error(resp)

    def download_file_content(
        self,
        object_id: str,
        filename: str,
        *,
        attribute_name: Optional[str] = None,
        position: Optional[int] = None,
    ) -> bytes:
        url = build_url(self.base_url, f"/object/{object_id}/file/{filename}/content")
        params = merge_params({"attribute_name": attribute_name}, {"position": position})
        resp = self.session.get(url, params=params, timeout=self.timeout, stream=True)
        if resp.status_code != 200:
            self._raise_api_error(resp)
        return resp.content

        def upload_file(
            self,
            object_id: str,
            file_path: str,
            *,
            attribute_name: Optional[str] = None,
            filename: Optional[str] = None,
    ) -> None:
        """
        POST /object/{object_id}/file

        Upload a file matching Postman's approach but letting requests handle Content-Type.
        """
        import os
        import mimetypes

        url = build_url(self.base_url, f"/object/{object_id}/file")

        # Build query parameters exactly as documented
        params = {}
        if attribute_name is not None:
            params["attribute_name"] = attribute_name
        if filename is not None:
            params["filename"] = filename

        # Determine actual filename for the upload
        actual_filename = filename or os.path.basename(file_path)

        # Guess MIME type from file extension (like Postman does)
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'

        # Save original headers
        original_content_type = self.session.headers.get('Content-Type')

        # Remove Content-Type so requests can set it with proper boundary
        self.session.headers.pop('Content-Type', None)

        try:
            # Prepare multipart/form-data with MIME type like Postman
            with open(file_path, "rb") as file_handle:
                files = [
                    ('file', (actual_filename, file_handle, mime_type))
                ]

                resp = self.session.post(
                    url,
                    params=params or None,
                    files=files,
                    timeout=self.timeout
                )

            if resp.status_code != 200:
                self._raise_api_error(resp)

        finally:
            # Restore original Content-Type
            if original_content_type is not None:
                self.session.headers['Content-Type'] = original_content_type

    def update_file(
            self,
            object_id: str,
            file_path: str,
            *,
            attribute_name: Optional[str] = None,
            filename: Optional[str] = None,
            position: Optional[int] = None,
    ) -> None:
        """
        PUT /object/{object_id}/file

        Update a file matching Postman's approach but letting requests handle Content-Type.
        """
        import os
        import mimetypes

        url = build_url(self.base_url, f"/object/{object_id}/file")

        # Build query parameters exactly as documented
        params = {}
        if attribute_name is not None:
            params["attribute_name"] = attribute_name
        if filename is not None:
            params["filename"] = filename
        if position is not None:
            params["position"] = position

        # Determine actual filename for the upload
        actual_filename = filename or os.path.basename(file_path)

        # Guess MIME type from file extension (like Postman does)
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'

        # Save original headers
        original_content_type = self.session.headers.get('Content-Type')

        # Remove Content-Type so requests can set it with proper boundary
        # (Different from upload - update endpoint may behave differently)
        self.session.headers.pop('Content-Type', None)

        try:
            # Prepare multipart/form-data with MIME type like Postman
            with open(file_path, "rb") as file_handle:
                files = [
                    ('file', (actual_filename, file_handle, mime_type))
                ]

                resp = self.session.put(
                    url,
                    params=params or None,
                    files=files,
                    timeout=self.timeout
                )

            if resp.status_code != 200:
                self._raise_api_error(resp)

        finally:
            # Restore original Content-Type
            if original_content_type is not None:
                self.session.headers['Content-Type'] = original_content_type

    def delete_file(
        self,
        object_id: str,
        *,
        filename: Optional[str] = None,
        attribute_name: Optional[str] = None,
        position: Optional[int] = None,
    ) -> None:
        url = build_url(self.base_url, f"/object/{object_id}/file")
        params = merge_params({"filename": filename}, {"attribute_name": attribute_name}, {"position": position})
        resp = self.session.delete(url, params=params, timeout=self.timeout)
        if resp.status_code != 200:
            self._raise_api_error(resp)

    # --------------------------------------------------------------------- #
    # Object versioning and view switching
    # --------------------------------------------------------------------- #
    def to_version_by_id(self, object_id: str, version_id: str) -> None:
        url = build_url(self.base_url, f"/object/{object_id}/to-version-by-id/{version_id}")
        resp = self.session.post(url, timeout=self.timeout)
        if resp.status_code != 200:
            self._raise_api_error(resp)

    def to_version_by_date(self, object_id: str, date_iso: str) -> None:
        url = build_url(self.base_url, f"/object/{object_id}/to-version-by-date/{date_iso}")
        resp = self.session.post(url, timeout=self.timeout)
        if resp.status_code != 200:
            self._raise_api_error(resp)

    def switch_to_draft(self) -> bool:
        url = build_url(self.base_url, "/session/versions/to-draft")
        resp = self.session.get(url, timeout=self.timeout)
        return self._json_or_error(resp)

    def switch_to_release(self) -> bool:
        url = build_url(self.base_url, "/session/versions/to-release")
        resp = self.session.get(url, timeout=self.timeout)
        return self._json_or_error(resp)

    # --------------------------------------------------------------------- #
    # Locale
    # --------------------------------------------------------------------- #
    def get_locale(self) -> str:
        url = build_url(self.base_url, "/session/locale")
        resp = self.session.get(url, timeout=self.timeout)
        return self._text_or_error(resp)

    def get_locales(self) -> List[str]:
        url = build_url(self.base_url, "/session/locales")
        resp = self.session.get(url, timeout=self.timeout)
        return self._json_or_error(resp)

    def set_locale(self, language_tag: str) -> None:
        url = build_url(self.base_url, f"/session/locale/{language_tag}")
        resp = self.session.put(url, timeout=self.timeout)
        if resp.status_code != 200:
            self._raise_api_error(resp)

    # --------------------------------------------------------------------- #
    # Transactions
    # --------------------------------------------------------------------- #
    def begin_transaction(self) -> None:
        url = build_url(self.base_url, "/session/transaction/begin")
        resp = self.session.put(url, timeout=self.timeout)
        if resp.status_code == 409:
            raise ConflictError("A transaction is already open. Commit or rollback first.")
        if resp.status_code != 200:
            self._raise_api_error(resp)

    def commit_transaction(self) -> None:
        url = build_url(self.base_url, "/session/transaction/commit")
        resp = self.session.put(url, timeout=self.timeout)
        if resp.status_code == 409:
            raise TransactionError("No open transaction to commit.")
        if resp.status_code != 200:
            self._raise_api_error(resp)

    def rollback_transaction(self) -> None:
        url = build_url(self.base_url, "/session/transaction/rollback")
        resp = self.session.put(url, timeout=self.timeout)
        if resp.status_code == 409:
            raise TransactionError("No open transaction to rollback.")
        if resp.status_code != 200:
            self._raise_api_error(resp)

    # --------------------------------------------------------------------- #
    # Upload directory (server app dir)
    # --------------------------------------------------------------------- #
    def upload_to_appdir(self, file_path: str, *, folder: Optional[str] = None, overwrite: Optional[bool] = True) -> None:
        url = build_url(self.base_url, "/upload/file")
        params = merge_params({"folder": folder}, {"overwrite": overwrite})
        with open(file_path, "rb") as f:
            files = {"file": (file_path, f)}
            resp = self.session.post(url, params=params, files=files, timeout=self.timeout)
        if resp.status_code != 200:
            self._raise_api_error(resp)

    def download_from_appdir(self, name: str, *, folder: Optional[str] = None) -> bytes:
        url = build_url(self.base_url, "/upload/file")
        params = merge_params({"name": name}, {"folder": folder})
        resp = self.session.get(url, params=params, timeout=self.timeout, stream=True)
        if resp.status_code == 404:
            raise NotFoundError(f"File '{name}' not found in appdir")
        if resp.status_code != 200:
            self._raise_api_error(resp)
        return resp.content

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _json_or_error(self, resp: requests.Response):
        if 200 <= resp.status_code < 300:
            if not resp.content:
                return None
            return resp.json()
        self._raise_api_error(resp)

    def _text_or_error(self, resp: requests.Response) -> str:
        if 200 <= resp.status_code < 300:
            return resp.text
        self._raise_api_error(resp)

    def _raise_api_error(self, resp: requests.Response) -> None:
        status = resp.status_code
        msg = self._extract_error_message(resp)

        if status in (401, 403):
            # 401 can also occur w the session cookie expired.
            raise PermissionDenied(msg or "Permission denied / authentication required")
        if status == 404:
            raise NotFoundError(msg or "Resource not found")
        if status == 409:
            raise ConflictError(msg or "Conflict")
        if status in (400, 405):
            raise ValidationError(msg or "Validation error")
        if status >= 500:
            raise ServerError(msg or "Server error")

        raise AenClientError(f"HTTP {status}: {msg or 'Unexpected error'}")

    @staticmethod
    def _extract_error_message(resp: requests.Response) -> Optional[str]:
        try:
            data = resp.json()
            if isinstance(data, dict):
                return data.get("message") or data.get("error") or data.get("detail")
        except Exception:
            pass
        return resp.text or None
