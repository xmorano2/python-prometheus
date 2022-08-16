import os
import imp
import sys
import json
import time
import logging
import datetime
import requests  # Available in 3.7+
#import subprocess
from datetime import date
#from http.client import HTTPSConnection # Available in 2.7 or v3.4+



# There are five levels, from the highest urgency to lowest urgency, are: 
#   CRITICAL, ERROR, WARNING, INFO, DEBUG
logging.basicConfig(level=logging.WARNING)

# Get VARs from SO
if os.getenv("SECRET"):
    secret = os.getenv("SECRET")
    logging.info ("From OS get SECRET [" + secret + "]")
else:
    print ("SECRET variable not defined, you need to export it")
    print ("export SECRET=`oc get secret -n openshift-monitoring | grep  prometheus-k8s-token | head -n 1 | awk '{ print $1 }'`")
    exit (1)

logging.info ("SECRET [" + str(secret) + "]")

if os.getenv("TOKEN"):
    token = os.getenv("TOKEN")
    logging.info ("From OS get TOKEN [" + token + "]")
else:
    print ("TOKEN variable not defined, you need to export it")
    print ("export TOKEN=`echo $(oc get secret $SECRET -n openshift-monitoring -o json | jq -r '.data.token') | base64 -d`")
    exit (1)

logging.info ("\nTOKEN [" + str(token) + "]")

if os.getenv("PROMETHEUS_HOST"):
    prometheus_host = os.getenv("PROMETHEUS_HOST")
    logging.info ("From OS get PROMETHEUS_HOST [" + prometheus_host + "]")
else:
    print ("PROMETHEUS_HOST variable not defined, you need to export it")
    print ("export PROMETHEUS_HOST=`oc get route prometheus-k8s -n openshift-monitoring -o json | jq -r '.spec.host'`")
    exit (1)

logging.info ("PROMETHEUS [" + str(prometheus_host) + "]")


my_date = datetime.date.today() 
year, week_num, day_of_week = my_date.isocalendar()
print("Week #" + str(week_num) + " of year " + str(year))

today = date.today()
start = today - datetime.timedelta(days=7) # today.weekday())
end = today + datetime.timedelta(days=-1) #today.weekday(), weeks=1)

print("Today:", today)
print("Querying statistics for this period:")
print("\tStart date : [" + str(start) + "]")
print("\tEnd date   : [" + str(end) + "]")
print ("-" * 33)

# https://developpaper.com/python-calls-prometheus-to-monitor-data-and-calculate/


# export SECRET=`oc get secret -n openshift-monitoring | grep  prometheus-k8s-token | head -n 1 | awk '{ print $1 }'`
# export TOKEN=`echo $(oc get secret $SECRET -n openshift-monitoring -o json | jq -r '.data.token') | base64 -d`
# export PROMETHEUS_HOST=`oc get route prometheus-k8s -n openshift-monitoring -o json | jq -r '.spec.host'`
# curl -fks "https://$PROMETHEUS_HOST/api/v1/query?query=haproxy_server_current_sessions" -H "Authorization: Bearer $TOKEN" |jq

def getPrometheusData (query):
    # Midnight at the end of the previous month.
    #end_of_month = datetime.datetime.today().replace(day=1).date()

    # Last day of the previous month.
    #last_day = end_of_month - datetime.timedelta(days=1)

    #duration = '[' + str(last_day.day) + 'd]'

    headers = { 'Authorization' : 'Bearer %s' %  token }
    response = requests.get('https://' + prometheus_host + '/api/v1/query',
      params={
                'query' : query,
                'start' : start,
                'end'   : end,
    
            },
        headers = headers,
        verify = False)
    
    results = response.json()['data']['result']

    return (results)

# ********************************************
# ********************************************
# ********************************************

data = {}


# Get CPU usage

results = getPrometheusData ('sum by(namespace) (rate(container_cpu_usage_seconds_total{container!="",container_name!="POD"}[5m]))')

for result in results:
    namespace = result['metric']['namespace']
    value = result['value'][1]
    if namespace not in data:
        data[namespace] = {}
        data[namespace]['namespace'] = namespace
        data[namespace]['cpu'] = '0'
        data[namespace]['mem'] = '0'
    data[namespace]['cpu'] = value or '0'

# Get MEM usage

results = getPrometheusData ('sum by(pod, namespace) (rate(container_memory_usage_bytes{container!="",container_name!="POD"}[5m]))')

for result in results:
    namespace = result['metric']['namespace']
    value = result['value'][1]
    if namespace not in data:
        data[namespace] = {}
        data[namespace]['namespace'] = namespace
        data[namespace]['cpu'] = '0'
        data[namespace]['mem'] = '0'
    value = result['value'][1] or '0'
    data[namespace]['mem'] = value


# Get Namespace's labels

results = getPrometheusData ('kube_namespace_labels')

get_labels = ('project_name', 'billing_utrkey', 'billing_tcfkey')
for result in results:
    namespace = result['metric']['namespace']
    labels = result['metric']
    if namespace not in data:
        data[namespace] = {}
        data[namespace]['namespace'] = namespace
        data[namespace]['cpu'] = '0'
        data[namespace]['mem'] = '0'
    for label in get_labels:
        if ("label_" + label) in labels:
            data[namespace][label] = labels["label_" + label]
        else:
            data[namespace][label] = ''


# File to store statistics, append mode

filename = "/var/tmp/statistics.csv"
file = open (filename, "a")

print ("%4s | %20s | %20s | %50s | %25s | %20s | %15s | %15s | %15s" % ('week', 'start date', 'end date', 'namespace', 'cpu', 'mem', 'Project Name', 'Billing TCFKey', 'Billing UTRKey'))
print ("-" * 208)
for namespace in data:
    file.write ("%d,%s,%s,%s,%s,%s,%s,%s,%s\n" % (
            week_num,
            start,
            end,
            namespace, 
            data[namespace]['cpu'],
            data[namespace]['mem'], 
            data[namespace]['project_name'],
            data[namespace]['billing_tcfkey'],
            data[namespace]['billing_utrkey'])
    )

    print ("%4d | %20s | %20s | %50s | %25s | %20s | %15s | %15s | %15s" % (
            week_num,
            start,
            end,
            namespace, 
            data[namespace]['cpu'],
            data[namespace]['mem'], 
            data[namespace]['project_name'],
            data[namespace]['billing_tcfkey'],
            data[namespace]['billing_utrkey'])
    )

file.close()

print ("\n\n")
print ("---------------------------------------")
print ("Statistics stored in [" + filename + "]")
print ("---------------------------------------")

