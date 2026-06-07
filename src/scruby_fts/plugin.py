# Scruby-FTS - Full-text search with Manticore Search.
# Copyright (c) 2026 Gennady Kostyunin
# SPDX-License-Identifier: MIT
# SPDX-License-Identifier: GPL-3.0-or-later
"""Plugin for full-text search."""

from __future__ import annotations

__all__ = ("FullTextSearch",)


import uuid
import warnings
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from threading import Event
from typing import Any, final

import manticoresearch
import orjson
from anyio import Path
from scruby import Scruby, ScrubyConfig
from scruby_plugin import ScrubyPlugin

from scruby_fts.config import FTSConfig


@final
class FullTextSearch(ScrubyPlugin):
    """Plugin for Scruby based on Manticore Search."""

    def __init__(self, scruby_self: Scruby) -> None:  # noqa: D107
        ScrubyPlugin.__init__(self, scruby_self)

    @classmethod
    async def delete_orphaned_tables(cls) -> None:
        """Delete unnecessary tables that remain due to errors."""
        db_id = ScrubyConfig.db_id
        config = FTSConfig.config
        async with manticoresearch.ApiClient(config) as api_client:
            utils_api = manticoresearch.UtilsApi(api_client)
            tables = await utils_api.sql(f"SHOW TABLES LIKE 'scruby_{db_id}%'")
            oneof_schema_1_validator = tables.oneof_schema_1_validator
            if oneof_schema_1_validator is not None:
                data = oneof_schema_1_validator[0]["data"]
                for item in data:
                    await utils_api.sql(f"DROP TABLE IF EXISTS {item['Table']}")

    @staticmethod
    async def _task_find(
        branch_number: int,
        morphology: str,
        full_text_filter: tuple[str, str],
        filter_fn: Callable,
        hash_reduce_left: str,
        db_root: str,
        class_model: Any,
        config: manticoresearch.configuration.Configuration,
        db_id: str,
        stop_event: Event,
    ) -> list[Any] | None:
        """Task for finding documents, using full-text search.

        This method is for internal use.

        Returns:
            List of documents or None.
        """
        # Suppress warning - RuntimeWarning: coroutine 'Find._task_find' was never awaited
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        # Variable initialization
        branch_number_as_hash: str = f"{branch_number:08x}"[hash_reduce_left:]  # pyrefly: ignore[bad-index]
        separated_hash: str = "/".join(list(branch_number_as_hash))
        leaf_path = Path(
            *(
                db_root,
                class_model.__name__,
                separated_hash,
                "leaf.json",
            ),
        )
        docs: list[Any] = []
        if await leaf_path.exists():
            data_json: bytes = await leaf_path.read_bytes()
            data: dict[str, str] = orjson.loads(data_json) or {}
            table_name: str = f"scruby_{db_id}_{str(uuid.uuid4())[:8]}"
            text_field_name: str = full_text_filter[0]
            table_field: str = f"{text_field_name} text"
            search_query = manticoresearch.SearchQuery(
                query_string=f"@{text_field_name} {full_text_filter[1]}",
            )
            search_request = manticoresearch.SearchRequest(
                table=table_name,
                query=search_query,
            )
            # Enter a context with an instance of the API client
            async with manticoresearch.ApiClient(config) as api_client:
                # Create instances of API classes
                index_api = manticoresearch.IndexApi(api_client)
                search_api = manticoresearch.SearchApi(api_client)
                utils_api = manticoresearch.UtilsApi(api_client)
                try:
                    # Create table
                    await utils_api.sql(f"CREATE TABLE {table_name}({table_field}) morphology = '{morphology}'")
                    # Start search
                    for _, val in data.items():
                        if stop_event.is_set():
                            await utils_api.sql(f"DROP TABLE IF EXISTS {table_name}")
                            return None
                        doc = class_model.model_validate_json(val)
                        if filter_fn(doc):
                            text_field_content = getattr(doc, text_field_name)
                            # Performs a search on a table
                            insert_request = manticoresearch.InsertDocumentRequest(
                                table=table_name,
                                doc={text_field_name: text_field_content or ""},
                            )
                            await index_api.insert(insert_request)
                            search_response = await search_api.search(search_request)
                            if len(search_response.hits.hits) > 0:
                                docs.append(doc)
                            # Clear table
                            await utils_api.sql(f"TRUNCATE TABLE {table_name}")
                finally:
                    # Delete table
                    await utils_api.sql(f"DROP TABLE IF EXISTS {table_name}")
        return docs or None

    async def find_one(
        self,
        morphology: str,
        full_text_filter: tuple[str, str],
        filter_fn: Callable = lambda _: True,
    ) -> Any | None:
        """Find a one document that matches the filter, using full-text search.

        Attention:
            - The search is based on the effect of a quantum loop.
            - The search effectiveness depends on the number of processor threads.

        Args:
            morphology (str): String with morphology of language.
            full_text_filter (tuple[str, str]): Filter for full-text search.
                                                full_text_filter[0] -> name of text field.
                                                full_text_filter[1] -> query string.
            filter_fn (Callable): A function that execute the conditions of filtering.

        Returns:
            Document or None.
        """
        # Get Scruby instance
        scruby_self = self.scruby_self()
        # Variable initialization
        search_task_fn: Callable = self._task_find
        branch_numbers: range = range(scruby_self._max_number_branch)
        hash_reduce_left: int = scruby_self._hash_reduce_left
        db_root: str = scruby_self._db_root
        class_model: Any = scruby_self._class_model
        stop_signal = Event()
        doc: Any | None = None
        config = FTSConfig.config
        db_id = scruby_self._db_id
        # Run quantum loop
        with ThreadPoolExecutor(scruby_self._max_workers) as executor:
            futures: list[Future] = [
                executor.submit(
                    search_task_fn,
                    branch_number,
                    morphology,
                    full_text_filter,
                    filter_fn,
                    hash_reduce_left,
                    db_root,
                    class_model,
                    config,
                    db_id,
                    stop_signal,
                )
                for branch_number in branch_numbers
            ]
            for future in as_completed(futures):
                docs = await future.result()
                if docs is not None:
                    # Get first document
                    doc = docs[0]
                    # Cancel all pending tasks in the queue instantly
                    executor.shutdown(wait=False, cancel_futures=True)
                    # Trigger the event to tell running tasks to exit
                    stop_signal.set()
                    # Stop loop
                    break
        # Return document
        return doc

    async def find_many(
        self,
        morphology: str,
        full_text_filter: tuple[str, str],
        filter_fn: Callable = lambda _: True,
        limit_docs: int = 100,
        page_number: int = 1,
        sort_fn: Callable | None = lambda doc: doc.created_at,
        sort_reverse: bool = True,
    ) -> list[Any] | None:
        """Find the many of documents that match the filter, using full-text search.

        Attention:
            - The search is based on the effect of a quantum loop.
            - The search effectiveness depends on the number of processor threads.

        Args:
            morphology (str): String with morphology of language.
            full_text_filter (tuple[str, str]): Filter for full-text search.
                                                full_text_filter[0] -> name of text field.
                                                full_text_filter[1] -> text query.
            filter_fn (Callable): A function that execute the conditions of filtering.
                                  By default it searches for all documents.
            limit_docs (int): Limiting the number of documents. By default = 100.
            page_number (int): For pagination. By default = 1.
                               Number of documents per page = limit_docs.
            sort_fn (Callable | None): Sort the list of documents.
                                       By default, documents are sorted by creation date.
            sort_reverse: (bool): Sorting direction.
                                  By default, sort descending (newest to oldest).

        Returns:
            List of documents or None.
        """
        # The `page_number` parameter must not be less than one
        assert page_number > 0, "`find_many` => The `page_number` parameter must not be less than one."
        # Get Scruby instance
        scruby_self = self.scruby_self()
        # Variable initialization
        search_task_fn: Callable = self._task_find
        branch_numbers: range = range(scruby_self._max_number_branch)
        hash_reduce_left: int = scruby_self._hash_reduce_left
        db_root: str = scruby_self._db_root
        class_model: Any = scruby_self._class_model
        stop_signal = Event()
        stop_outer_loop: bool = False
        config = FTSConfig.config
        db_id = scruby_self._db_id
        counter: int = 0
        number_docs_skippe: int = limit_docs * (page_number - 1) if page_number > 1 else 0
        result: list[Any] = []
        # Run quantum loop
        with ThreadPoolExecutor(scruby_self._max_workers) as executor:
            futures: list[Future] = [
                executor.submit(
                    search_task_fn,
                    branch_number,
                    morphology,
                    full_text_filter,
                    filter_fn,
                    hash_reduce_left,
                    db_root,
                    class_model,
                    config,
                    db_id,
                    stop_signal,
                )
                for branch_number in branch_numbers
            ]
            for future in as_completed(futures):
                docs = await future.result()
                if docs is not None:
                    for doc in docs:
                        if number_docs_skippe == 0:
                            if counter >= limit_docs:
                                # Cancel all pending tasks in the queue instantly
                                executor.shutdown(wait=False, cancel_futures=True)
                                # Trigger the event to tell running tasks to exit
                                stop_signal.set()
                                # Stop loops
                                stop_outer_loop = True
                                break
                            result.append(doc)
                            counter += 1
                        else:
                            number_docs_skippe -= 1
                if stop_outer_loop:
                    break
        # Sorting
        if sort_fn is not None:
            result.sort(key=sort_fn, reverse=sort_reverse)
        # Return a document list
        return result or None
