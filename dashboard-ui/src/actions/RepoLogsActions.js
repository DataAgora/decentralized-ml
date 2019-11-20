import Reflux from 'reflux';

var RepoLogsActions = Reflux.createActions({
  fetchRepoLogs: {children: ['completed', 'failed'], asyncResult: true},
});

export default RepoLogsActions;
