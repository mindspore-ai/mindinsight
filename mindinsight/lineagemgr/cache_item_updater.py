# Copyright 2020 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""Cache item updater."""
import os

from mindinsight.datavisual.data_transform.data_manager import BaseCacheItemUpdater, CachedTrainJob
from mindinsight.lineagemgr.common.log import logger
from mindinsight.lineagemgr.common.exceptions.exceptions import LineageFileNotFoundError
from mindinsight.lineagemgr.common.validator.validate import validate_train_id, validate_added_info
from mindinsight.lineagemgr.lineage_parser import LineageParser, LINEAGE
from mindinsight.utils.exceptions import ParamValueError


def update_lineage_object(data_manager, train_id, added_info: dict):
    """Update lineage objects about tag and remark."""
    validate_train_id(train_id)
    validate_added_info(added_info)
    cache_item = data_manager.get_brief_train_job(train_id)
    lineage_item = cache_item.get(key=LINEAGE, raise_exception=False)
    if lineage_item is None or lineage_item.super_lineage_obj is None:
        logger.warning("Cannot update the lineage for tran job %s, because it does not exist.", train_id)
        raise ParamValueError("Cannot update the lineage for tran job %s, because it does not exist." % train_id)

    cached_added_info = lineage_item.super_lineage_obj.added_info
    new_added_info = dict(cached_added_info)

    for key, value in added_info.items():
        new_added_info.update({key: value})

    with cache_item.lock_key(LINEAGE):
        cache_item.get(key=LINEAGE).super_lineage_obj.added_info = new_added_info


class LineageCacheItemUpdater(BaseCacheItemUpdater):
    """Cache item updater for lineage info."""

    def update_item(self, cache_item: CachedTrainJob):
        """Update cache item in place."""
        summary_base_dir = cache_item.summary_base_dir
        summary_dir = cache_item.abs_summary_dir

        # The summary_base_dir and summary_dir have been normalized in data_manager.
        if summary_base_dir == summary_dir:
            relative_path = "./"
        else:
            relative_path = f'./{os.path.basename(summary_dir)}'

        try:
            lineage_parser = self._lineage_parsing(cache_item)
        except LineageFileNotFoundError:
            self._delete_lineage_in_cache(cache_item, LINEAGE, relative_path)
            return

        cache_item.set(key=LINEAGE, value=lineage_parser)

    def _lineage_parsing(self, cache_item):
        """Parse summaries and return lineage parser."""
        train_id = cache_item.train_id
        summary_dir = cache_item.abs_summary_dir
        update_time = cache_item.basic_info.update_time

        cached_lineage_item = cache_item.get(key=LINEAGE, raise_exception=False)
        if cached_lineage_item is None:
            lineage_parser = LineageParser(train_id, summary_dir, update_time)
        else:
            lineage_parser = cached_lineage_item
            with cache_item.lock_key(LINEAGE):
                lineage_parser.update_time = update_time
                lineage_parser.load()

        return lineage_parser

    def _delete_lineage_in_cache(self, cache_item, key, relative_path):
        with cache_item.lock_key(key):
            try:
                cache_item.delete(key=key)
                logger.info("Parse failed, delete the tran job %s.", relative_path)
            except ParamValueError:
                logger.debug("Parse failed, and it is not in cache, "
                             "no need to delete the train job %s.", relative_path)
