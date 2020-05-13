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
from mindinsight.lineagemgr.querier.query_model import LineageObj
from mindinsight.lineagemgr.summary.lineage_summary_analyzer import LineageSummaryAnalyzer


class LineageCacheItemUpdater(BaseCacheItemUpdater):
    """Cache item updater for lineage info."""

    def update_item(self, cache_item: CachedTrainJob):
        """Update cache item in place."""
        log_path = cache_item.summary_dir
        log_dir = os.path.dirname(log_path)
        lineage_info = LineageSummaryAnalyzer.get_summary_infos(log_path)
        user_defined_info = LineageSummaryAnalyzer.get_user_defined_info(log_path)
        lineage_obj = LineageObj(
            log_dir,
            train_lineage=lineage_info.train_lineage,
            evaluation_lineage=lineage_info.eval_lineage,
            dataset_graph=lineage_info.dataset_graph,
            user_defined_info=user_defined_info
        )
        cache_item.set(key="lineage", value=lineage_obj)
