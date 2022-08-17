# Summary

Here you will find how to get statistics from Prometheus to get the namespace consumption for cpu, memory and labels associated.

As the data gathered is taken using three different Prometheus queries, a consolidation will also need to obtain only one report with all the data.

You can get the statistics using two different options:
- **Option 1**: Using [Python](#option-1-using-python) as described below to obtain the report in one step, just executing [this program](prom.py)
- **Option 2**: From [command line](#option-2-command-line), and using curl and join programs as shown below.

Both options should be executed on every cluster, and must have access to the *oc* command to get the needed parameters to connect to the Prometheus API.

# Option 1: Using Python

This [Python program](prom.py) uses the Prometheus API rest to get the data using three different queries:
* cpu: \
    `sum by(namespace) (rate(container_cpu_usage_seconds_total{container!="",container_name!="POD"}[5m]))`
* memory: \
    `sum by(namespace) (rate(container_memory_usage_bytes{container!="",container_name!="POD"}[5m]))`
* labels: \
    `kube_namespace_labels`

The data is extracted and consolidated for each namespace and stored in the file /var/tmp/statistics.csv in append mode.

## Prerequisites

This Python program uses libraries that requires at least Python version 2.7.5

To connect to the Prometheus API, using the **[OpenShift command-line interface (CLI)](https://docs.openshift.com/container-platform/4.10/cli_reference/openshift_cli/getting-started-cli.html)** this program will need the url of the Prometheus API server and also the authorization token to use.

You will need to execute the following exports before running the Python program: 
```
    # export SECRET=`oc get secret -n openshift-monitoring | grep  prometheus-k8s-token | head -n 1 | awk '{ print $1 }'`
    # export TOKEN=`echo $(oc get secret $SECRET -n openshift-monitoring -o json | jq -r '.data.token') | base64 -d`
    # export PROMETHEUS_HOST=`oc get route prometheus-k8s -n openshift-monitoring -o json | jq -r '.spec.host'`
```

## How to run this program

This program allows to specify three optional parameters:
```
usage: prom.py [-h] [--start START_DATE] [--end END_DATE] [--cluster CLUSTER_NAME]

optional arguments:
  -h, --help              show this help message and exit
  --start START_DATE      Start date to get statistics (YYYY-MM-DD)
  --end END_DATE          End date to get statistics (YYYY-MM-DD)
  --cluster CLUSTER_NAME  Cluster name
```

If you don't specify the cluster name, *local* will be used.
If you don't specify the start date, it will be calculated as 'today - 7 days'
If you don't specify the end date, it will today's date.
    
As a result of the programs execution, the file /var/tmp/statistics.csv will be extended with the data for the given period. An example of the information gathered in the file can be found [here](example_data.txt)

```
# Example data file generated
# Column description:
#   cluster name
#   start date 
#   end date
#   namespace
#   cpu
#   mem
#   project name
#   billing TCFKey
#   billing UTRKey
#
local,2022-07-25 00:00:00,2022-07-31 00:00:00,openshift-vsphere-infra,0,0,,,
local,2022-07-25 00:00:00,2022-07-31 00:00:00,openshift-cluster-samples-operator,0.0015044444000000428,360594.3615650139,,,
local,2022-07-25 00:00:00,2022-07-31 00:00:00,openshift-monitoring,0.4745672153185268,472678.4,,,
local,2022-07-25 00:00:00,2022-07-31 00:00:00,kube-system,0.0036524612296296955,550039.1401608866,PRJ-21941,TCFKey-9439,UTRKey-13507
local,2022-07-25 00:00:00,2022-07-31 00:00:00,openshift-azure-operator,0.0038263943185184095,0,PRJ-18113,TCFKey-28258,UTRKey-14383
local,2022-07-25 00:00:00,2022-07-31 00:00:00,openshift-cluster-csi-drivers,0.015752900348148156,1939820.088888889,PRJ-24205,TCFKey-23676,UTRKey-15168
local,2022-07-25 00:00:00,2022-07-31 00:00:00,openshift-authentication-operator,0.024151080233333167,4182076.6814814815,PRJ-5732,TCFKey-20978,UTRKey-10201
```

# Option 2: Command line

If you want to get the statistics for memory, cpu, and labels without using Python, here you have the commands needed:
* Extract the data using curl
* Consolidate into one file

## Prerequisites

As a prerequisite to connect to the Prometheus API, first we'll need to know the url of the Prometheus API server and also the authorization token to use.

Using the **[OpenShift command-line interface (CLI)](https://docs.openshift.com/container-platform/4.10/cli_reference/openshift_cli/getting-started-cli.html)** this program will get the information commented above:
* Prometheus server url
* Authorized token

To do so, you can execute: 
```
    # export SECRET=`oc get secret -n openshift-monitoring | grep  prometheus-k8s-token | head -n 1 | awk '{ print $1 }'`
    # export TOKEN=`echo $(oc get secret $SECRET -n openshift-monitoring -o json | jq -r '.data.token') | base64 -d`
    # export PROMETHEUS_HOST=`oc get route prometheus-k8s -n openshift-monitoring -o json | jq -r '.spec.host'`
    # curl -fks "https://$PROMETHEUS_HOST/api/v1/query?query=haproxy_server_current_sessions" -H "Authorization: Bearer $TOKEN" |jq
```

**Note**: The kubeconfig file must be available under the same node from which the required # oc commands will be run, and \
    `export KUBECONFIG=<kubeconfig_path>/kubeconfig` \
should be run before the oc commands

## Run queries from command line

First we need to set the start and end dates to get the data:
```
    # start day, 7 days ago
    START=`date -I -d "-7 days"`
    # end date, today
    END=`date -I`
```

    
The queries could also be executed from command line, using curl to access the Prometheus API:
* cpu: \
    `curl -g -k --data-urlencode "start=${START}" --data-urlencode "end=${END}" "https://$PROMETHEUS_HOST/api/v1/query?query=sum%20by(namespace)(rate(container_cpu_usage_seconds_total{namespace!=''}[5m]))" -H "Authorization: Bearer $TOKEN"  | jq -r '.data.result[] | [.metric.namespace, .value[1]] | @tsv' | sort -k1 > cpu.tsv`

* memory: \
    `curl -g -k --data-urlencode "start=${START}" --data-urlencode "end=${END}" "https://$PROMETHEUS_HOST/api/v1/query?query=sum%20by(namespace)(rate(container_memory_usage_bytes{namespace!=''}[5m]))" -H "Authorization: Bearer $TOKEN"  | jq -r '.data.result[] | [.metric.namespace, .value[1]] | @tsv' | sort -k1 > memory.tsv`

* labels: \
    `curl -k --data-urlencode "start=${START}" --data-urlencode "end=${END}" "https://$PROMETHEUS_HOST/api/v1/query?query=kube_namespace_labels" -H "Authorization: Bearer $TOKEN" | jq -r '.data.result[] | [.metric.namespace, .metric.label_billing_tcfkey, .metric.label_billing_utrkey, .metric.label_project_name] | @tsv' | sort -k1 > labels.tsv`

## Consolidate the results

And to consolidate the three files using the namespace as a joiner: \
    `join -j 1 cpu.tsv memory.tsv | join -j 1 - labels.tsv > totals.tsv`


# Authors

The Red Hat Customer Success team

# Disclaimer

THIS SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THIS SOFTWARE OR THE USE OR OTHER DEALINGS IN THIS SOFTWARE.




