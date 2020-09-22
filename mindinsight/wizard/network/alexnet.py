# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""alexnet module."""
from mindinsight.wizard.network.generic_network import GenericNetwork


class Network(GenericNetwork):
    """Network code generator."""
    name = 'alexnet'
    supported_datasets = ['Cifar10', 'ImageNet']
    supported_loss_functions = ['SoftmaxCrossEntropyWithLogits']
    supported_optimizers = ['Momentum', 'Adam', 'SGD']
