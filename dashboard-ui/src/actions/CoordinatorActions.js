import Reflux from 'reflux';

var CoordinatorActions = Reflux.createActions({
  fetchCoordinatorStatus: {children: ['completed', 'failed'], asyncResult: true},
});

export default CoordinatorActions;
