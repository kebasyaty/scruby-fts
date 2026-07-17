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
from typing import Any, Never, assert_never, final

import manticoresearch
from scruby import Scruby, ScrubyConfig
from scruby.cache import DocCache
from scruby.mixins.find import ReturnType
from scruby_plugin import ScrubyPlugin

from scruby_fts.config import FTSConfig


@final
class FullTextSearch(ScrubyPlugin):
    """Plugin for Scruby based on Manticore Search."""

    def __init__(self, scruby_self: Scruby) -> None:  # ruff:ignore[undocumented-public-init]
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
        morphology: str,
        full_text_filter: tuple[str, str],
        filter_fn: Callable,
        db_id: str,
        hash_reduce_left: int,
        branch_number: int,
        class_model: Any,
        stop_event: Event,
        config: manticoresearch.configuration.Configuration,
    ) -> list[Any] | None:
        """Task for finding documents, using full-text search.

        This method is for internal use.

        Returns:
            List of documents or None.
        """
        # Suppress warning - RuntimeWarning: coroutine 'Find._task_find' was never awaited
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        # Variable initialization
        collection_name = class_model.__name__
        branch_number_as_hash: str = f"{branch_number:08x}"[hash_reduce_left:]  # pyrefly: ignore[bad-index]
        docs: dict[str, Any] = {}
        result: list[Any] = []

        match hash_reduce_left:
            case 7:
                docs = DocCache.cache[collection_name][branch_number_as_hash[0]]
            case 6:
                docs = DocCache.cache[collection_name][branch_number_as_hash[0]][branch_number_as_hash[1]]
            case 5:
                docs = DocCache.cache[collection_name][branch_number_as_hash[0]][branch_number_as_hash[1]][
                    branch_number_as_hash[2]
                ]
            case _:
                msg = "Scruby.run() > Parameter: `hash_reduce_left` -> Valid values are Literal[7, 6, 5]."
                raise AssertionError(msg)

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
                for _, doc in docs.items():
                    if stop_event.is_set():
                        await utils_api.sql(f"DROP TABLE IF EXISTS {table_name}")
                        return None
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
                            result.append(doc)
                        # Clear table
                        await utils_api.sql(f"TRUNCATE TABLE {table_name}")
            finally:
                # Delete table
                await utils_api.sql(f"DROP TABLE IF EXISTS {table_name}")
        return result or None

    async def find_one(
        self,
        morphology: str,
        full_text_filter: tuple[str, str],
        filter_fn: Callable = lambda _: True,
        return_type: ReturnType = ReturnType.MODEL,
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
            return_type (ReturnType): ScrubyModel, JSON-string or Dictionary.

        Returns:
            Document or None.
        """
        # Get Scruby instance
        scruby_self = self.scruby_self()

        # Variable initialization
        hash_reduce_left: int = scruby_self._hash_reduce_left
        assert hash_reduce_left != 0, (
            "Scruby.run(hash_reduce_left = 0) - Not valid for `plugins.fullTextSearch.find_one` method."
        )
        search_task_fn: Callable = self._task_find
        branch_numbers: range = range(scruby_self._max_number_branch)
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
                    morphology,
                    full_text_filter,
                    filter_fn,
                    db_id,
                    hash_reduce_left,
                    branch_number,
                    class_model,
                    stop_signal,
                    config,
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
        match return_type.value:
            case 1:
                return doc
            case 2:
                return doc.model_dump_json() if doc is not None else None
            case 3:
                return doc.model_dump() if doc is not None else None
            case _ as unreachable:
                assert_never(Never(unreachable))  # pyrefly: ignore[not-callable]

    async def find_many(
        self,
        morphology: str,
        full_text_filter: tuple[str, str],
        filter_fn: Callable = lambda _: True,
        limit_docs: int = 100,
        page_number: int = 1,
        sort_fn: Callable | None = lambda doc: doc.created_at,
        sort_reverse: bool = True,
        return_type: ReturnType = ReturnType.MODEL,
    ) -> list[Any] | str | None:
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
            return_type (ReturnType): ScrubyModel, JSON-string or Dictionary.

        Returns:
            List of documents or None.
        """
        # The `page_number` parameter must not be less than one
        assert page_number > 0, "`find_many` => The `page_number` parameter must not be less than one."

        # Get Scruby instance
        scruby_self = self.scruby_self()

        # Variable initialization
        hash_reduce_left: int = scruby_self._hash_reduce_left
        assert hash_reduce_left != 0, (
            "Scruby.run(hash_reduce_left = 0) - Not valid for `plugins.fullTextSearch.find_many` method."
        )
        search_task_fn: Callable = self._task_find
        branch_numbers: range = range(scruby_self._max_number_branch)
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
                    morphology,
                    full_text_filter,
                    filter_fn,
                    db_id,
                    hash_reduce_left,
                    branch_number,
                    class_model,
                    stop_signal,
                    config,
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
        match return_type.value:
            case 1:
                return result or None
            case 2:
                return f"[{','.join([doc.model_dump_json() for doc in result])}]" if result is not None else None
            case 3:
                return [doc.model_dump() for doc in result] if result is not None else None
            case _ as unreachable:
                assert_never(Never(unreachable))  # pyrefly: ignore[not-callable]
