# from core.utils.dmljob import serialize_job, deserialize_job

class DMLResult(object):
    """
    DML Result

    This class is created by the Runners whenever they're done running a job,
    and it's passed to the Communication Manager on success or back to the
    Scheduler on error.

    TODO: Right now the DMLResult object is passing around the DMLJob that
    originated the results, but we can do better.

    """

    def __init__(
        self,
        status,
        job,
        results={},
        error_message="",
    ):
        """
        Initializes a DML Result object.

        Args:
            status (str): status of the job [successful|failed].
            job (DMLJob): the job that finished running.
            results (dict): results from running the job.
            error_message (str): error message of why the job failed (if it did).
        """
        self.status = status
        self.job = job
        self.results = results
        self.error_message = error_message

# NOTE: If this class ever becomes more useful than a dictionary,
# steps should be taken to reimplement this functionality.

# def serialize_result(dmlresult_job):
#     """
#     Serializes a DML Result object into a dictionary.

#     Args:
#         dmlresult_job (DMLResult): result object.

#     Returns:
#         dict: The serialized version of the DML Result.
        
#     """
#     return {
#         'status': dmlresult_job.status,
#         'job': serialize_job(dmlresult_job.job),
#         'results': dmlresult_job.results,
#         'error_message': dmlresult_job.error_message,
#     }


# def deserialize_result(serialized_result):
#     """
#     Deserializes a serialized version of a DML Result object.

#     Args:
#         serialized_result (dict): serialized version of a DML Result object.

#     Returns:
#         DMLResult: A DML Result object from serialized_result.
#     """
#     return DMLResult(
#         status=serialized_result['status'],
#         job=deserialize_job(serialized_result['job']),
#         results=serialized_result['results'],
#         error_message=serialized_result['error_message'],
#     )
