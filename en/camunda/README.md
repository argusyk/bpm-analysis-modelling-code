# An Executable Model in Camunda 8 (Practicum for Chapter 9)

**Note.** The files in this folder were prepared according to the official Camunda 8 documentation, but they
were not run in the environment where the textbook was created (there was no Docker or Java). The commands for
starting Camunda depend on the platform version; before the practicum, check them against the current documentation: https://docs.camunda.io/

## Steps

1. Install Camunda 8 Run (a lightweight local distribution, Java 21 required) following the instructions
   "Run Camunda 8 locally" on docs.camunda.io, or use a Camunda SaaS cloud trial cluster.
2. Open models/aerocargo-tobe.bpmn in Camunda Modeler, switch the model to Camunda 8
   and make it executable: for the validation service task (in the file it is a business rule task)
   set the job type `validate-awb` (Task definition → Type), and forms for the user tasks.
3. Deploy the model with the Deploy button (Camunda 8 Self-Managed, the cluster address from the Camunda 8 Run documentation).
4. Start the worker: `pip install pyzeebe` and `python worker.py`.
5. Create a process instance (the Run button in Modeler or the REST API, see Section 7.4.2 of the textbook)
   with the variables the worker expects, for example
   `{"awb": "176-12345675", "pieces": 12, "declaredWeightKg": 412}`,
   and follow it in Operate; perform the user tasks in Tasklist.
