import Reflux from 'reflux';

var DashboardActions = Reflux.createActions({
  fetchAllRepos: {children: ['completed', 'failed'], asyncResult: true}
});

export default DashboardActions;
