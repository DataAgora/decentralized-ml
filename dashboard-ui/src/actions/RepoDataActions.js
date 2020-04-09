import Reflux from 'reflux';

var RepoDataActions = Reflux.createActions({
  createNewRepo: {children: ['completed', 'failed'], asyncResult: true},
  fetchRepoData: {children: ['completed', 'failed'], asyncResult: true},
  fetchReposRemaining: {children: ['completed', 'failed'], asyncResult: true},
  resetState: {children: ['completed', 'failed'], asyncResult: true},
  deleteRepo: {children: ['completed', 'failed'], asyncResult: true}
});

export default RepoDataActions;