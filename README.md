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

This Python program uses libraries that requires at least Python version 3.4

To connect to the Prometheus API, using the **[OpenShift command-line interface (CLI)](https://docs.openshift.com/container-platform/4.10/cli_reference/openshift_cli/getting-started-cli.html)** this program will get the url of the Prometheus API server and also the authorization token to use.

The *oc* commands used are:
* get the secret containing the token: \
    `oc get secret -n openshift-monitoring | grep  prometheus-k8s-token | head -n 1 | awk '{ print $1 }'`
* get the token inside the above secret: \
    `oc get secret " + secret + " -n openshift-monitoring -o json | jq -r '.data.token' | base64 -d`
* get the Prometheus host: \
    `oc get route prometheus-k8s -n openshift-monitoring -o json | jq -r '.spec.host'`

If you want to test the data gathered, you can execute: 
```
    # export SECRET=`oc get secret -n openshift-monitoring | grep  prometheus-k8s-token | head -n 1 | awk '{ print $1 }'`
    # export TOKEN=`echo $(oc get secret $SECRET -n openshift-monitoring -o json | jq -r '.data.token') | base64 -d`
    # export PROMETHEUS_HOST=`oc get route prometheus-k8s -n openshift-monitoring -o json | jq -r '.spec.host'`
    # curl -fks "https://$PROMETHEUS_HOST/api/v1/query?query=haproxy_server_current_sessions" -H "Authorization: Bearer $TOKEN" |jq
```

**Note**: The kubeconfig file must be available under the same node from which the required # oc commands will be run using this Python program, and \
    `export KUBECONFIG=<kubeconfig_path>/kubeconfig` \
should be run before the Python program is executed

## How to run this program

This program should be executed every Monday, to get the statistics for the past week (Monday to Sunday) and store them in a text file in a separated comma format.

To execute it using the system crontab, add the following line to execute the Python program every Monday, at 09:00 AM
```
0  9 * * 1 export KUBECONFIG=<kubeconfig_path>/kubeconfig && python </home/of/the/script>/prom.py >> /tmp/prom.log 2>&1
```

You can also execute it by hand just invoking it from command line: \
    `python prom.py`
    
As a result of the programs execution, the file /var/tmp/statistics.csv will be extended with the data for the given period. An example of the information gathered in the file can be found [here](example_data.txt)

```
# Example data file generated
# Column description:
#   number of week
#   start date 
#   end date
#   namespace
#   cpu
#   mem
#   project name
#   billing TCFKey
#   billing UTRKey
#
32,2022-07-25 00:00:00,2022-07-31 00:00:00,openshift-vsphere-infra,0,0,,,
32,2022-07-25 00:00:00,2022-07-31 00:00:00,openshift-cluster-samples-operator,0.0015044444000000428,360594.3615650139,,,
32,2022-07-25 00:00:00,2022-07-31 00:00:00,openshift-monitoring,0.4745672153185268,472678.4,,,
32,2022-07-25 00:00:00,2022-07-31 00:00:00,kube-system,0.0036524612296296955,550039.1401608866,PRJ-21941,TCFKey-9439,UTRKey-13507
32,2022-07-25 00:00:00,2022-07-31 00:00:00,openshift-azure-operator,0.0038263943185184095,0,PRJ-18113,TCFKey-28258,UTRKey-14383
32,2022-07-25 00:00:00,2022-07-31 00:00:00,openshift-cluster-csi-drivers,0.015752900348148156,1939820.088888889,PRJ-24205,TCFKey-23676,UTRKey-15168
32,2022-07-25 00:00:00,2022-07-31 00:00:00,openshift-authentication-operator,0.024151080233333167,4182076.6814814815,PRJ-5732,TCFKey-20978,UTRKey-10201
32,2022-07-25 00:00:00,2022-07-31 00:00:00,openshift-operator-lifecycle-manager,0.015337990403703539,599214.4592592593,,,
32,2022-07-25 00:00:00,2022-07-31 00:00:00,openshift-network-diagnostics,0.004193588188888926,248566.5185185185,,,
32,2022-07-25 00:00:00,2022-07-31 00:00:00,openshift-cloud-credential-operator,0.0024220056999999275,2118345.0074074077,PRJ-7638,TCFKey-3390,UTRKey-13884
32,2022-07-25 00:00:00,2022-07-31 00:00:00,openshift-machine-api,0.008486375925925969,385994.9037037037,,,
32,2022-07-25 00:00:00,2022-07-31 00:00:00,openshift-cloud-controller-manager-operator,0.0017692133629629502,583383.1202500704,PRJ-7311,TCFKey-24512,UTRKey-4350
32,2022-07-25 00:00:00,2022-07-31 00:00:00,openshift-image-registry,0.0071573309592592406,711581.3925925926,,,
32,2022-07-25 00:00:00,2022-07-31 00:00:00,openshift-cluster-node-tuning-operator,0.0019464917185185067,0,PRJ-16105,TCFKey-13115,UTRKey-3581
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




