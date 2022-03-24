# Copyright 2020-2021 Huawei Technologies Co., Ltd
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
"""Modelarts notebook module."""
import json
import os
import random
import argparse
import shlex
import logging
import uuid
import subprocess

import mindinsight
from mindinsight.scripts.start import Command
from mindinsight.utils.log import setup_logger
from mindinsight.modelarts.utils.utils import get_notebook_registry


logger = setup_logger("notebook", "notebook", console=True, level=logging.INFO)

_OK = 0
_NOK = 1
_REUSE = 2

try:
    import html

    html_escape = html.escape
    del html
except ImportError:
    import cgi

    html_escape = cgi.escape
    del cgi


# Return values for `_get_context` (see that function's docs for details).
_CONTEXT_IPYTHON = "_CONTEXT_IPYTHON"
_CONTEXT_NONE = "_CONTEXT_NONE"


def _get_context():
    """
    Determine the most specific context that we're in.

    Returns:
      str: in an IPython notebook context (e.g., from running `jupyter notebook` at the command line).
      str: Otherwise (e.g., by running a Python script at the
        command-line or using the `ipython` interactive shell).
    """
    try:
        import IPython
    except ImportError:
        pass
    else:
        if IPython.get_ipython() is not None:
            # We'll assume that we're in a notebook context.
            return _CONTEXT_IPYTHON

    # In an IPython command line shell or Jupyter notebook, we can
    # directly query whether we're in a notebook context.
    try:
        import IPython
    except ImportError:
        pass
    else:
        ipython = IPython.get_ipython()
        if ipython is not None and ipython.has_trait("kernel"):
            return _CONTEXT_IPYTHON

    # Otherwise, we're not in a known notebook context.
    return _CONTEXT_NONE


def notebook_load_ipython_extension(ipython):
    """
    Load the MindInsight notebook extension.

    Intended to be called from `%load_ext mindinsight`. Do not invoke this directly.

    Args:
      ipython(ipykernel.zmqshell.ZMQInteractiveShell): An `IPython.InteractiveShell` instance.
    """
    _register_magics(ipython)


def _register_magics(ipython):
    """
    Register IPython line/cell magics.

    Args:
      ipython(ipykernel.zmqshell.ZMQInteractiveShell): An `InteractiveShell` instance.
    """
    ipython.register_magic_function(
        _start_magic, magic_kind="line", magic_name="mindinsight",
    )


def _start_magic(line):
    """Implementation of the `%mindinsight` line magic."""
    if os.environ.get('BASE_URL', None) is None:
        return print("MindInsight is not supported in the current environment!")
        
    return start(line)

def start(args_string):
    """
    Launch and display a MindInsight instance as if at the command line.

    Args:
      args_string(str): Command-line arguments to MindInsight, to be
        interpreted by `shlex.split`: e.g., "--summary-base-dir ./logs --port 8080".
        Shell metacharacters are not supported: e.g., "--summary-base-dir 2>&1" will
        point the summary-base-dir at the literal directory named "2>&1".
    """
    parsed_args = shlex.split(args_string, comments=True, posix=True)

    parser = argparse.ArgumentParser(
        prog='mindinsight',
        description='MindInsight CLI entry point (version: {})'.format(mindinsight.__version__),
        allow_abbrev=False)

    notebook_command = Command()
    notebook_command.add_arguments(parser=parser)
    args = parser.parse_args(parsed_args)

    context = _get_context()
    try:
        import IPython
        import IPython.display
    except ImportError:
        IPython = None

    if context == _CONTEXT_NONE:
        handle = None
        logger.info("Launching MindInsight...")
    else:
        handle = IPython.display.display(
            IPython.display.Pretty("Launching MindInsight in Notebook..."), display_id=True,
        )

    input_path = ''
    port = 8080
    for key, value in args.__dict__.items():
        if key == 'summary_base_dir' and value:
            input_path = value
        if key == 'port' and value:
            port = int(value)

    notebook_register = get_notebook_registry()
    if notebook_register:
        args_string = notebook_register.start(args_string, port=port, input_path=input_path)

    cmd = 'mindinsight start {}'.format(args_string)
    process = subprocess.Popen(
        shlex.split(cmd),
        shell=False,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    process.wait()
    mindinsight_stdout = process.stdout.read().decode('utf-8')
    if process.returncode == _OK or process.returncode == _REUSE:
        if process.returncode == _OK:
            logger.info(f'mindinsight start on port {port}')
        if process.returncode == _REUSE:
            logger.info("{}".format(mindinsight_stdout))
        display(port=port)
    else:
        logger.info("{}".format(mindinsight_stdout))


def display(port=None, height=None):
    """
    Display a MindInsight instance already running on this machine.

    Args:
      port(Union[None, int]): The port on which the MindInsight server is listening, as an
        `int`, or `None` to automatically select the most recently
        launched MindInsight.
      height(Union[None, int]): The height of the frame into which to render the MindInsight
        UI, as an `int` number of pixels, or `None` to use a default value
        (currently 800).
    """
    _display(port=port, height=height, display_handle=None)


def _display(port=None, height=None, display_handle=None):
    """
    Internal version of `display`.

    Args:
      port(Union[None, int]): As with `display`.
      height(Union[None, int]): As with `display`.
      display_handle(NoneType): If not None, an IPython display handle into which to
        render MindInsight.
    """
    if height is None:
        height = 800

    if port is None:
        port = 8080

    fn = {
        _CONTEXT_IPYTHON: _display_ipython,
        _CONTEXT_NONE: _display_cli,
    }[_get_context()]
    return fn(port=port, height=height, display_handle=display_handle)


def _display_ipython(port, height, display_handle):
    import IPython.display

    frame_id = "mindinsight-frame-{:08x}".format(random.getrandbits(64))
    shell = """
      <iframe id="%HTML_ID%" width="100%" height="%HEIGHT%" frameborder="0">
      </iframe>
      <script>
        (function() {
          const frame = document.getElementById(%JSON_ID%);
          const url = new URL(%URL%, window.location);
          const port = %PORT%;
          if (port) {
            url.port = port;
          }
          frame.src = url;
        })();
      </script>
    """
    # proxy_url should be constructed from ``{base_url}/proxy/{port}``
    base_url = os.environ.get('BASE_URL') if 'BASE_URL' in os.environ and os.environ['BASE_URL'] else ''
    default_proxy_url = base_url + '/proxy/%PORT%/'
    proxy_url = os.environ.get('PROXY_URL') if 'PROXY_URL' in os.environ and os.environ[
        'PROXY_URL'] else default_proxy_url

    if proxy_url is not None:
        # Allow %PORT% in $PROXY_URL
        proxy_url = proxy_url.replace("%PORT%", "%d" % port)
        replacements = [
            ("%HTML_ID%", html_escape(frame_id, quote=True)),
            ("%JSON_ID%", json.dumps(frame_id)),
            ("%HEIGHT%", "%d" % height),
            ("%PORT%", "0"),
            ("%URL%", json.dumps(proxy_url)),
        ]
    else:
        replacements = [
            ("%HTML_ID%", html_escape(frame_id, quote=True)),
            ("%JSON_ID%", json.dumps(frame_id)),
            ("%HEIGHT%", "%d" % height),
            ("%PORT%", "%d" % port),
            ("%URL%", json.dumps("/")),
        ]

    for (k, v) in replacements:
        shell = shell.replace(k, v)
    iframe = IPython.display.HTML(shell)
    if display_handle:
        display_handle.update(iframe)
    else:
        IPython.display.display(iframe)


def _display_cli(port, height, display_handle):
    del height  # unused
    del display_handle  # unused
    message = "Please visit http://localhost:%d in a web browser." % port
    logger.info(message)
