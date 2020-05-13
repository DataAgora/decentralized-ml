import CoordinatorActions from "./../actions/CoordinatorActions"
import RepoLogsActions from "./../actions/RepoLogsActions"


var repoIds = new Set();
var timerOn = false;

function startTimer() {
  repoIds = new Set();
  timerOn = true;
  updateRepoStatuses()
}

function updateRepoStatuses() {
  for (let repoId of repoIds) {
    CoordinatorActions.fetchCoordinatorStatus(repoId)
    RepoLogsActions.fetchRepoLogs(repoId)
  }
  setTimeout(updateRepoStatuses, 5000)
}

function trackRepoStatus(repoId, stopTracking) {
  if (!timerOn) {
    startTimer()
  }

  if (stopTracking) {
    repoIds.delete(repoId)
  } else {
    repoIds.add(repoId)
  }
}

export default trackRepoStatus;
