import Reflux from 'reflux';
import CoordinatorActions from './../actions/CoordinatorActions';
import AuthStore from './AuthStore';
import Endpoints from './../constants/endpoints.js';


class CoordinatorStore extends Reflux.Store {

  constructor () {
    super();
    this.init();
    this.listenables = CoordinatorActions;
  }

  init () {
    this.state = {
      loading: true, // not used
      error: false, // not used
      coordinatorStatuses: {},
    };
  }

  onFetchCoordinatorStatus(repoId) {
    if (AuthStore.state.isAuthenticated) {
      let jwtString = AuthStore.state.jwt;

      this.state.loading = true;
      this._changed();

      fetch(
        Endpoints["dashboardFetchCoordinatorStatus"] + repoId, {
          method: 'GET',
          headers: {
            'Content-Type':'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + jwtString,
          },
        }
      ).then(response => {
        this._handleResponse(repoId, response, CoordinatorActions.fetchCoordinatorStatus);
      });
    }
  }

  _handleResponse(repoId, response, refluxAction) {
    response.json().then(serverResponse => {
      if (response.status === 200) {
        refluxAction.completed(repoId, serverResponse);
      } else {
        // TODO: Use error returned by server.
        refluxAction.failed(repoId, serverResponse);
      }
    });
  }

  onFetchCoordinatorStatusCompleted (repoId, status) {
    this.state.coordinatorStatuses[repoId] = status;
    this.state.loading = false;
    this._changed();
  }

  onFetchCoordinatorStatusFailed (repoId, errorObject) {
    this.state.coordinatorStatuses[repoId] = {};
    this.state.error = errorObject["message"];
    this.state.loading = false;
    this._changed();
  }

  _changed () {
    this.trigger(this.state);
  }

}

export default CoordinatorStore;
