import Reflux from 'reflux';
import RepoLogsActions from './../actions/RepoLogsActions';
import AuthStore from './AuthStore';
import Endpoints from './../constants/endpoints.js';


class RepoLogsStore extends Reflux.Store {

  constructor () {
    super();
    this.init();
    this.listenables = RepoLogsActions;
  }

  init () {
    this.state = {
      loadingLogs: true,
      errorLogs: false,
      repoLogs: [],
    };
  }

  onFetchRepoLogs(repoId) {
    if (AuthStore.state.isAuthenticated) {
      let jwtString = AuthStore.state.jwt;

      this.state.loadingLogs = true;
      this._changed();

      fetch(
        Endpoints["dashboardFetchRepoLogs"] + repoId, {
          method: 'GET',
          headers: {
            'Content-Type':'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + jwtString,
          },
        }
      ).then(response => {
        this._handleResponse(response, RepoLogsActions.fetchRepoLogs);
      });
    }
  }

  _handleResponse(response, refluxAction) {
    response.json().then(serverResponse => {
      if (response.status === 200) {
        refluxAction.completed(serverResponse);
      } else {
        // TODO: Use error returned by server.
        refluxAction.failed(serverResponse);
      }
    });
  }

  onFetchRepoLogsCompleted (repoLogs) {
    this.state.repoLogs = repoLogs;
    this.state.loadingLogs = false;
    this._changed();
  }

  onFetchRepoLogsFailed (errorObject) {
    this.state.repoLogs = {};
    this.state.errorLogs = errorObject["Message"];
    this.state.loadingLogs = false;
    this._changed();
  }

  _changed () {
    this.trigger(this.state);
  }

}

export default RepoLogsStore;
