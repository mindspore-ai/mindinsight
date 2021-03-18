# TensorFlow model exporting

[查看中文](./tensorflow_model_exporting_cn.md)

If build model with Keras API, user can try the following methods.

For TensorFlow 1.15.x version:

```python
import tensorflow as tf
from tensorflow.python.framework import graph_io
from tensorflow.python.keras.applications.inception_v3 import InceptionV3


def freeze_graph(graph, session, output_nodes, output_folder: str):
    """
    Freeze graph for tf 1.x.x.

    Args:
        graph (tf.Graph): Graph instance.
        session (tf.Session): Session instance.
        output_nodes (list): Output nodes name.
        output_folder (str): Output folder path for frozen model.
    """
    with graph.as_default():
        graphdef_inf = tf.graph_util.remove_training_nodes(graph.as_graph_def())
        graphdef_frozen = tf.graph_util.convert_variables_to_constants(session, graphdef_inf, output_nodes)
        graph_io.write_graph(graphdef_frozen, output_folder, "frozen_model.pb", as_text=False)


tf.keras.backend.set_learning_phase(0)

keras_model = InceptionV3()
session = tf.keras.backend.get_session()

INPUT_NODES = [ipt.op.name for ipt in keras_model.inputs]
OUTPUT_NODES = [opt.op.name for opt in keras_model.outputs]
freeze_graph(session.graph, session, OUTPUT_NODES, "/home/user/xxx")
print(f"Input nodes name: {INPUT_NODES}, output nodes name: {OUTPUT_NODES}")
```

For TensorFlow 2.x.x version:

```python
import tensorflow as tf
from tensorflow.python.framework.convert_to_constants import convert_variables_to_constants_v2


def convert_to_froze_graph(keras_model: tf.python.keras.models.Model, model_name: str,
                           output_folder: str):
    """
    Export keras model to frozen model.

    Args:
        keras_model (tensorflow.python.keras.models.Model): Model instance.
        model_name (str): Model name for the file name.
        output_folder (str): Output folder for saving model.
    """
    full_model = tf.function(lambda x: keras_model(x))
    full_model = full_model.get_concrete_function(
        tf.TensorSpec(keras_model.inputs[0].shape, keras_model.inputs[0].dtype)
    )

    frozen_func = convert_variables_to_constants_v2(full_model)
    frozen_func.graph.as_graph_def()

    print(f"Model inputs: {frozen_func.inputs}")
    print(f"Model outputs: {frozen_func.outputs}")

    tf.io.write_graph(graph_or_graph_def=frozen_func.graph,
                      logdir=output_folder,
                      name=model_name,
                      as_text=False)
```
