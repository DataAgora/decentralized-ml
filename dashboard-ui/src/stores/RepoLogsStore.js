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
      loading: false,
      repoLogs: {},
      error: "",
    };
  }

  onFetchRepoLogs(repoId) {
    if (AuthStore.state.isAuthenticated) {
      let jwtString = AuthStore.state.jwt;

      fetch(
        Endpoints.dashboardFetchRepoLogs + repoId, {
          method: 'GET',
          headers: {
            'Content-Type':'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + jwtString,
          },
        }
      ).then(response => {
        this._handleResponse(response, RepoLogsActions.fetchRepoLogs, repoId);
      });
    }
  }

  _handleResponse(response, refluxAction, repoId) {
    response.json().then(serverResponse => {
      if (serverResponse.error) {
        refluxAction.failed(serverResponse.message, repoId);
      } else {
        refluxAction.completed(serverResponse.message, repoId);
      }
    });
  }

  onFetchRepoLogsCompleted (repoLogs, repoId) {
    this.state.repoLogs[repoId] = repoLogs;
    this._changed();
  }

  onFetchRepoLogsFailed (error, repoId) {
    this.state.repoLogs[repoId] = [];
    this.state.error = error
    console.log(error);
    this._changed();
  }

  _changed () {
    this.trigger(this.state);
  }
}

export default RepoLogsStore;
