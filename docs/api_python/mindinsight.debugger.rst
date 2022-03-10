mindinsight.debugger
====================

MindSpore调试器是为图模式训练提供的调试工具，可以用来查看并分析计算图节点的中间结果。 在MindSpore图模式的训练过程中，用户无法方便地获取到计算图中间节点的结果，使得训练调试变得很困难。

使用MindSpore调试器，用户可以：在MindInsight调试器界面结合计算图，查看图节点的输出结果；设置监测点，监测训练异常情况（比如检查张量溢出），在异常发生时追踪错误原因；查看权重等参数的变化情况；查看图节点和源代码的对应关系。

调试器API是为离线调试提供的Python API接口，使用之前需要先保存Dump数据。保存Dump数据的方法参考 `使用Dump功能在Graph模式调试 <https://www.mindspore.cn/docs/programming_guide/zh-CN/master/dump_in_graph_mode.html>`_ 。

.. py:class:: mindinsight.debugger.DumpAnalyzer(dump_dir, mem_limit=None)

    用来检查Dump数据的分析器。

    .. warning::
        此类中的所有API均为实验版本，将来可能更改或者删除。

    **参数：**

    - **dump_dir** (str) - 存储Dump数据文件的目录。
    - **mem_limit** (int, optional) - 检查监测点的内存限制(以MB为单位)。默认值：None，表示没有限制。可选值：从2048MB到2147483647MB。

    .. py:method:: check_watchpoints(watchpoints, error_on_value=False)

        批量检查指定迭代上指定节点上的给定监测点。

        .. note::
            1. 为了提升速度，应该同时给出迭代下的所有监测点，避免多次读取张量。
            2. check_watchpoints函数在调用的时候会启动新的进程，需要通过”if __main__ == '__main__'“进行调用。

        **参数：**

        - **watchpoints** (Iterable[Watchpoint]) - 监测点列表。
        - **error_on_no_value** (bool) - 当指定的张量没有存储在dump_dir路径中时，是否抛出监测点命中错误码。默认值:False。

        **返回：**

        Iterable[WatchpointHit]，监测点命中列表，并按张量落盘时间排序。

    .. py:method:: export_graphs(output_dir=None)

        将计算图导入到output_dir路径下的xlsx文件中。

        这些文件将包含图节点的堆栈信息。

        **参数：**

        - **output_dir** (str, optional) - 保存文件的输出目录。默认值：None，表示使用当前的工作目录。

        **返回：**

        str，生成文件的路径。

    .. py:method:: get_input_nodes(node)

        获取指定节点的输入节点信息。

        **参数：**

        - **node** (Node) - 指定节点。

        **返回：**

        Iterable[Node]，指定节点的输入节点。

    .. py:method:: get_iterations(ranks=None)

        获取有Dump数据的迭代序号列表。

        **参数：**

        - **ranks** (Union[int, list[int], None], optional) - 指定逻辑卡号。如果设置成None，将返回所有逻辑卡的迭代序号列表。默认值：None。

        **返回：**

        Iterable[int]，有Dump数据的迭代序号列表，按从小到大排序。

    .. py:method:: get_output_nodes(node)

        获取指定节点的输出节点。

        **参数：**

        - **node** (Node) - 指定节点。

        **返回：**

        Iterable[Node]，该节点的输出节点。

    .. py:method:: get_ranks()

        获取有Dump数据的逻辑卡号列表。

        **返回：**

        Iterable[int]，当前Dump目录中的逻辑卡号列表。

    .. py:method:: list_affected_nodes(tensor)

        列出使用指定张量作为输入的节点。

        受影响的节点定义是指使用给定张量作为输入的节点。如果一个节点受到给定张量的影响，那么当给定的张量发生变化时，该节点的输出值很可能会发生变化。

        **参数：**

        - **tensor** (DebuggerTensor) - 指定张量。

        **返回：**

        Iterable[Node]，受指定张量影响的节点。

    .. py:method:: select_nodes(query_string, use_regex=False, select_by="node_name", ranks=None, case_sensitive=True)

        选择节点。

        根据节点名称或节点堆栈信息选择符合要求的节点。节点可以通过"node_name"或"code_stack"进行匹配，具体用法请参考参数说明。

        **参数：**

        - **query_string** (str) - 查询字符串。对于要选择的节点，匹配目标字段必须包含或能匹配到查询的字符串。
        - **use_regex** (bool) - 是否对目标字段按照查询字符串进行正则匹配。默认值：False。
        - **select_by** (str, optional) - 选择节点所依赖的字段。可用值为“node_name”、“code_stack”。“node_name”表示根据节点的名称进行筛选。“code_stack”表示对系欸但的堆栈信息进行筛选。默认值：“node_name”。
        - **ranks** (Union[int, list[int], None], optional) -  要选择的逻辑卡号或者逻辑卡号列表。选定的节点必须存在于指定的逻辑卡上。默认值：None，这意味着将考虑所有逻辑卡。
        - **case_sensitive** (bool, optional) - 对目标字段进行匹配时是否区分大小写。默认值：True。

        **返回：**

        Iterable[Node]，匹配的节点。

    .. py:method:: select_tensors(query_string, use_regex=False, select_by="node_name", iterations=None, ranks=None, slots=None, case_sensitive=True)

        选择张量。

        根据query_string选择目录中匹配的张量。张量可以通过“node_name”或“code_stack”进行匹配，具体用法请参考参数说明。

        **参数：**

        - **query_string** (str) - 查询字符串。对于要选择的张量，匹配目标字段必须包含或能匹配到查询字符串。
        - **use_regex** (bool) - 指明查询对象是否为正则表达式。默认值：False。
        - **select_by** (str, optional) - 选择张量时要搜索的字段。可用值为“node_name”、“code_stack”。“node_name”表示在图中搜索张量的节点名称。“code_stack”表示输出该张量的节点的堆栈信息。默认值：“node_name”。
        - **iterations** (Union[int, list[int], None], optional) - 要选择的迭代对象。默认值：None，表示选择保存的所有迭代。
        - **ranks** (Union[int, list[int], None], optional) - 要选择的逻辑卡号或逻辑卡号列表。默认值：None，这意味着将选择所有逻辑卡。
        - **slots** (list[int], optional) -  所选张量的编号。默认值：None，这意味着将选择所有编号。
        - **case_sensitive** (bool, optional) - 选择张量时是否区分大小写。默认值：True。

        **返回：**

        Iterable[DebuggerTensor]，匹配的张量。

.. py:class:: mindinsight.debugger.Node(node_feature)

    计算图中的节点。

    .. warning::
        此类中的所有API均为实验版本，将来可能更改或者删除。

    **参数：**

    - **node_feature** (namedtuple) - 节点特征。

      - **name** (str) - 节点名称。
      - **rank** (int) - 逻辑卡号。
      - **stack** (iterable[dict]) - 每一项的格式为：{'file_path': str, 'line_no': int, 'code_line': str}。
      - **graph_name** (str) - 图名称。
      - **root_graph_id** (int) - 根图id。

    .. py:method:: get_input_tensors(iterations=None, slots=None)

        获取该节点的输入张量。

        **参数：**

        - **iterations** (Iterable[int]) -  指定的迭代序号列表。默认值：None，这意味着将考虑所有可用的迭代。
        - **slots** (Iterable[int]) - 指定输入张量的编号列表。默认值：None，表示会返回所有的输入张量。

        **返回：**

        Iterable[DebuggerTensor]，节点的输入张量列表。

    .. py:method:: get_output_tensors(iterations=None, slots=None)

        获取该节点的输出张量。

        **参数：**

        - **iterations** (Iterable[int]) - 指定的迭代序号列表。默认值：None，这意味着将考虑所有可用的迭代。
        - **slots** (Iterable[int]) - 指定输出张量的编号列表。默认值：None，表示会返回所有的输出张量。

        **返回：**

        Iterable[DebuggerTensor]，节点的输出张量。

    .. py:method:: graph_name
        :property:

        获取当前节点的图名称。

        **返回：**

        str，图名称。

    .. py:method:: name
        :property:

        获取该节点的全名。

        **返回：**

        str，节点的全名。

    .. py:method:: rank
        :property:

        获取逻辑卡号。

        **返回：**

        int，节点所属的逻辑卡号。

    .. py:method:: root_graph_id
        :property:

        获取当前节点所属的根图id。

        **返回：**

        int，根图id。

    .. py:method:: stack
        :property:

        获取堆栈信息。

        **返回：**

        iterable[dict]，每一项的格式为{'file_path': str, 'line_no': int, 'code_line': str}。

.. py:class:: mindinsight.debugger.DebuggerTensor(node, slot, iteration)

    具有特定逻辑卡号，迭代序号和调试信息的张量。

    .. warning::
        此类中的所有API均为实验版本，将来可能更改或者删除。

    **参数：**

    - **node** (Node) - 输出此张量的节点。
    - **slot** (int) - 节点上张量的编号。
    - **iteration** (int) - 张量的迭代序号。

    .. note::
        用户不应该手动实例化此类。
        这个类的实例是不可修改的。
        DebuggerTensor始终是节点的输出张量。

    .. py:method:: iteration
        :property:

        获取张量的迭代。

        **返回：**

        int，张量的迭代序号。

    .. py:method:: node
        :property:

        获取输出此张量的节点。

        **返回：**

        Node，输出这个张量的节点。

    .. py:method:: rank
        :property:

        rank代表的是生成张量的设备逻辑卡的卡号。

        **返回：**

        int，生成张量的设备的逻辑卡的卡号。

    .. py:method:: slot
        :property:

        节点的输出可能有几个张量，slot指的是张量的编号。

        **返回：**

        int，节点上生成张量的编号。

    .. py:method:: value()

        获取张量的值。

        **返回：**

        Union[numpy.array, None]，如果在相关迭代中找不到数据文件，则该值可能为None。

.. py:class:: mindinsight.debugger.Watchpoint(tensors, condition)

    用来检查指定张量是否满足指定检查条件的监测点。

    .. warning::
        此类中的所有API均为实验版本，将来可能更改或者删除。

    **参数：**

    - **tensors** (Iterable[DebuggerTensor]) - 要检查的张量。
    - **condition** (ConditionBase) - 应用于张量的检查条件。

    .. py:method:: condition
        :property:

        获取应用于张量的检查条件。

        **返回：**

        ConditionBase，应用于张量的检查条件。

    .. py:method:: tensors
        :property:

        获取要检查的张量。

        **返回：**

        Iterable[DebuggerTensor])，要检查的张量。

.. py:class:: mindinsight.debugger.WatchpointHit

    监测点命中情况。

    .. warning::
        此类中的所有API均为实验版本，将来可能更改或者删除。

    .. note::
        此类不能由用户实例化。
        这个类的实例是无法修改的。

    .. py:method:: error_code
        :property:

        获取错误码，当检查到监测点发生错误时。返回对应的错误码，0表示没有错误发生。

        **返回：**

        int，错误码。

    .. py:method:: error_msg
        :property:

        如果出现错误，获取检查监测点过程中的错误信息。

        **返回：**

        list[str]，错误信息列表。

    .. py:method:: get_hit_detail()

        获取监测点中阈值的实际值。如果error_code不为零，则返回None。

        **返回：**

        Union[ConditionBase, None]，命中信息的条件，如果error_code不为零，则返回None。

    .. py:method:: get_threshold()

        获取用户设置的条件。

        **返回：**

        ConditionBase，包括用户阈值的检查条件。

    .. py:method:: tensor
        :property:

        获取监测点命中的张量。

        **返回：**

        DebuggerTensor，触发的张量。

.. py:class:: mindinsight.debugger.TensorTooLargeCondition(abs_mean_gt=None, max_gt=None, min_gt=None, mean_gt=None)

    张量过大的监测点。至少应该指定其中一个参数。

    当指定多个参数时，只要有一个参数满足检查条件，就会在检查后命中该监测点。

    .. warning::
        此类中的所有API均为实验版本，将来可能更改或者删除。

    **参数：**

    - **abs_mean_gt** (float, optional) - 张量绝对值的均值阈值。当实际值大于该阈值时，则满足该检查条件。
    - **max_gt** (float, optional) - 张量最大值的阈值。当实际值大于该阈值时，则满足该检查条件。
    - **min_gt** (float, optional) -  张量最小值的阈值。当实际值大于该阈值时，则满足该检查条件。
    - **mean_gt** (float, optional) - 张量均值的阈值。当实际值大于该阈值时，则满足该检查条件。

    .. py:method:: param_names
        :property:

        返回参数名称的列表。

        **返回：**

        list[str]，参数名称列表。

.. py:class:: mindinsight.debugger.TensorTooSmallCondition(abs_mean_lt=None, max_lt=None, min_lt=None, mean_lt=None)

    张量太小的监测点。至少应该指定其中一个参数。

    当指定多个参数时，只要有一个参数满足检查条件，就会在检查后命中该监测点。

    .. warning::
        此类中的所有API均为实验版本，将来可能更改或者删除。

    **参数：**

    - **abs_mean_lt** (float, optional) - 张量绝对值的均值阈值。当实际值小于该阈值时，则满足该检查条件。
    - **max_lt** (float, optional) - 张量最大值的阈值。当实际值小于该阈值时，则满足该检查条件。
    - **min_lt** (float, optional) -  张量最小值的阈值。当实际值小于该阈值时，则满足该检查条件。
    - **mean_lt** (float, optional) - 张量均值的阈值。当实际值小于该阈值时，则满足该检查条件。

    .. py:method:: param_names
        :property:

        返回参数名称的列表。

        **返回：**

        list[str]，参数名称。

.. py:class:: mindinsight.debugger.TensorRangeCondition(range_start_inclusive=None, range_end_inclusive=None, range_percentage_lt=None, range_percentage_gt=None, max_min_lt=None, max_min_gt=None)

    张量范围监测点。

    设置阈值以检查张量值范围。有四个选项：range_percentage_lt、range_percentage_gt、max_min_lt和max_min_gt。至少应指定四个选项之一。如果阈值设置为前两个选项之一，则必须设置 range_start_inclusive和range_end_inclusive。当指定多个参数时，只要有一个参数满足检查条件，就会在检查后命中该监测点。

    .. warning::
        此类中的所有API均为实验版本，将来可能更改或者删除。

    **参数：**

    - **range_percentage_lt** (float, optional) - 范围内张量百分比的阈值。当指定范围内张量的百分比小于该值时，将满足检查条件。
    - **range_percentage_gt** (float, optional) - 范围内张量百分比的阈值。当指定范围内张量的百分比大于该值时，将满足检查条件。
    - **max_min_lt** (float, optional) - 张量的最大值和最小值之差的下限阈值。
    - **max_min_gt** (float, optional) - 张量的最大值和最小值之差的上限阈值。
    - **range_start_inclusive** (float, optional) - 区间的开始。
    - **range_end_inclusive** (float, optional) - 区间的结束。

    .. py:method:: param_names
        :property:

        返回参数名称的列表。

        **返回：**

        list[str]，参数名称。

.. py:class:: mindinsight.debugger.TensorOverflowCondition

    张量溢出的监测点。

    张量溢出的监测点检查Inf和NaN张量。

    .. warning::
        此类中的所有API均为实验版本，将来可能更改或者删除。

    .. py:method:: param_dict
        :property:

        获取参数列表。

        **返回：**

        dict，检查条件的参数。

    .. py:method:: param_names
        :property:

        返回参数的名称列表。

        **返回：**

        list[str]，参数名称列表。

.. py:class:: mindinsight.debugger.OperatorOverflowCondition

    算子溢出的监测点。

    算子溢出监测点检查算子计算过程中是否发生溢出。仅支持昇腾AI处理器。

    .. warning::
        此类中的所有API均为实验版本，将来可能更改或者删除。

    .. py:method:: param_dict
        :property:

        获取参数列表。

        **返回：**

        dict，检查条件的参数。

    .. py:method:: param_names
        :property:

        返回参数的名称列表。

        **返回：**

        list[str]，参数名称列表。

.. py:class:: mindinsight.debugger.TensorAllZeroCondition(zero_percentage_ge)

    张量全零的监测点。

    .. warning::
        此类中的所有API均为实验版本，将来可能更改或者删除。

    **参数：**

    - **zero_percentage_ge** (float) - 检查零张量值的百分比是否大于此值的阈值。

    .. py:method:: param_names
        :property:

        返回参数名称列表。

        **返回：**

        list[str]，参数名称列表。

.. py:class:: mindinsight.debugger.TensorUnchangedCondition(rtol=1e-5, atol=1e-8)

    张量不变条件监测点。

    当满足所有指定的检查条件时，将在检查后命中该监测点。检查先前和当前张量的allclose函数。(abs_mean(current_tensor - previous_tensor) <= (atol + rtol * abs_mean(previous_tensor)))。

    .. warning::
        此类中的所有API均为实验版本，将来可能更改或者删除。

    **参数：**

    - **rtol** (float, optional) - 相对容差参数。默认值：1e-5。
    - **atol** (float, optional) - 绝对容差参数。默认值：1e-8。

    .. py:method:: param_names
        :property:

        返回参数名称列表。

        **返回：**

        list[str]，参数名称列表。

.. py:class:: mindinsight.debugger.TensorChangeBelowThresholdCondition(abs_mean_update_ratio_lt, epsilon=1e-9)

    低于阈值监测点的张量变化。

    当满足所有指定的检查条件时，将在检查后命中该监测点。(abs_mean(current_tensor - previous_tensor) < epsilon + mean_update_ratio_lt * abs_mean(previous_tensor))。

    .. warning::
        此类中的所有API均为实验版本，将来可能更改或者删除。

    **参数：**

    - **abs_mean_update_ratio_lt** (float) - 平均变化比例的阈值。如果平均更新率小于该值，则将触发监测点。
    - **epsilon** (float, optional) - Epsilon 值。默认值：1e-9。

    .. py:method:: param_names
        :property:

        返回参数名称列表。

        **返回：**

        list[str]，参数名称列表。

.. py:class:: mindinsight.debugger.TensorChangeAboveThresholdCondition(abs_mean_update_ratio_gt, epsilon=1e-9)

    高于阈值监测点的张量变化。

    当满足所有指定的检查条件时，将在检查后命中该监测点。(abs_mean(current_tensor - previous_tensor) > epsilon + mean_update_ratio_gt * abs_mean(previous_tensor))。

    .. warning::
        此类中的所有API均为实验版本，将来可能更改或者删除。

    **参数：**

    - **abs_mean_update_ratio_gt** (float) - 平均更新率的阈值，如果平均更新率大于此值，则将触发观察点。
    - **epsilon** (float, optional) - Epsilon 值。默认值：1e-9。

    .. py:method:: param_names
        :property:

        返回参数名称列表。

        **返回：**

        list[str]，参数名称列表。

.. py:class:: mindinsight.debugger.ConditionBase

    检查条件的基类。

    .. warning::
        此类中的所有API均为实验版本，将来可能更改或者删除。

    .. note::
        如果为一个条件实例指定了多个检查参数，只要有一个参数满足检查条件，就会在检查后命中该监测点。

    .. py:method:: condition_id
        :property:

        获取检查条件id的名称。

        **返回：**

        int， 检查条件的id。

    .. py:method:: name
        :property:

        获取检查条件的名称。

        **返回：**

        str， 检查条件的名称。

    .. py:method:: param_dict
        :property:

        获取检查条件的参数。

        **返回：**

        dict， 检查条件的参数。



