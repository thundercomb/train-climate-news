import sys
import datetime
import time
import kfp

kubeflow_host = sys.argv[1]
experiment_name = sys.argv[2]
pipeline_path = sys.argv[3]
datetime_now = f"{datetime.datetime.now():%Y%m%d_%H%M%S}"
job_name=f'{experiment_name}_training_{datetime_now}'

client = kfp.Client(host=kubeflow_host)
exp = client.create_experiment(name=f'{experiment_name}')
run = client.run_pipeline(experiment_id=exp.id,job_name=job_name,pipeline_package_path=pipeline_path)

print(f"RUN ID: {run.id}")

while(True):
    run_status = client.get_run(run.id).run.status
    if run_status == "":
        run_status = "Pending"

    print(f"Status : {run_status} ...", end=' ')
    if run_status == "Succeeded":
        print(f"\nSUCCESS: For details go to https://{kubeflow_host}/#/runs/details/{run.id}")
        break
    if run_status == "Failed" or run_status == "Error":
        print(f"\nFAILURE: For details go to https://{kubeflow_host}/#/runs/details/{run.id}")
        exit(1)

    print("sleeping for 5 seconds ...")
    time.sleep(5)
