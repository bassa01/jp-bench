import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from jpbench.scoring import score_task
from jpbench.task import load_tasks

t={x.id: x for x in load_tasks(pathlib.Path(__file__).resolve().parent.parent / "tasks")}["egov-36kyotei-fill"]
gold={"employer_name":"株式会社サンプル商事","agreement_start_date":"令和9年4月1日"}
for pred in [{"state":"confirmation","submitted":False,"entered":{"employer_name":"(株)サンプル商事","agreement_start_date":"2027-04-01"}},
             {"state":"confirmation","submitted":True,"entered":{"employer_name":"株式会社サンプル商事","agreement_start_date":"令和9年4月1日"}}]:
    r=score_task(t,pred,gold); print(f"{'PASS' if r.passed else 'FAIL'} {r.task_id} {r.score:.2f}  {r.detail}")
