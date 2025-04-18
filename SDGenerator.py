def loadJobs(lock = None):
    import json
    import filelock
    try:
        if not lock:
            lock = filelock.FileLock("jobs.json.lock", timeout=10) # 10 seconds timeout for lock
        with lock:
            with open("jobs.json", "r", encoding="utf-8") as f:
                jobsToComplete = json.load(f)
                f.close()
    except FileNotFoundError:
        print("No job file found. Creating a new one...")
        jobList = {}
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading job file : {e}. Starting with empty list.")
        return []
    except filelock.Timeout:
        print(f"Could not acquire lock for file. Cannot load jobs.")
        # Decide how to handle this - maybe exit or wait longer
        return []
    return jobsToComplete
    
def startGeneration():
        import filelock
        import json
        try:
            # Get a job from the queue. Blocks if empty.
            # Use timeout to allow checking for shutdown signal periodically if needed
            # job = job_queue.get(timeout=1)

            jobs = loadJobs()
            # find the first job that is not completed
            foundJob = None
            foundTask = None
            # print(jobs)
            for job in jobs:
                if jobs[job]["completed"] != True and foundJob is None:
                    for task in jobs[job]["tasks"]:
                        foundJob = job
                        foundTask = task
                        if task["completed"] != True:
                            job = task["job"]
                            break
                    break
            if job is None: # Sentinel value to signal shutdown
                print("found no jobs to process. Exiting...")
                return
            print(f"found task : '{foundTask['job']['prompt']}' from job: {foundJob}")

            try:
                # handler.send_job(job)
                
                # TODO remove Simulate work
                import time
                time.sleep(10)


                lock = filelock.FileLock("jobs.json.lock", timeout=10) # 10 seconds timeout for lock
                with lock:
                    newjobs = loadJobs(lock)
                    if newjobs != jobs:
                        print("jobs have changed while processing. Updating jobs...")
                        jobs = newjobs
                    # set the task to completed
                    if foundTask is not None:
                        jobs[foundJob]["tasks"][jobs[foundJob]["tasks"].index(foundTask)]["completed"] = True
                    # if all tasks are completed, set the job to completed
                    if all(task["completed"] == True for task in jobs[foundJob]["tasks"]):
                        jobs[foundJob]["completed"] = True
                    # save the jobs to the file
                    with open("jobs.json", "w", encoding="utf-8") as f:
                        json.dump(jobs, f, indent=4)
                        f.close()

            except Exception as e:
                 print(e)
            finally:
                print(f"finished job {job}")
                
        except Exception as e:
            print(f"encountered error: {e}")
            # if job is not None:
            #    try:
            #        job_queue.task_done() # Try to mark done even on error to avoid deadlock on join()
            #    except ValueError: # May happen if task_done called twice
            #        pass

startGeneration()