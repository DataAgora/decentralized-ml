import Reflux from 'reflux';
import RepoDataActions from './../actions/RepoDataActions';
import AuthStore from './AuthStore';
import Endpoints from './../constants/endpoints.js';


class RepoDataStore extends Reflux.Store {

  constructor () {
    super();
    this.init();
    this.listenables = RepoDataActions;
  }

  init () {
    this.state = {
      loading: true,
      error: false,

      repoWasFound: false,
      repoData: {},
      repoStatus: {},
      repoLogs: [],

      creationState: {
        reposRemaining: false,
        repoName: null,
        repoId: null,
        apiKey: null,
        loading: true,
        creating: false,
        created: false,
        error: false,
      },
    };
  }

  onShowModal() {
    this.state.creationState.created = true;
    this._changed();
    console.log(this.state.creationState);
  }

  onFetchRepoData(repoId) {
    if (AuthStore.state.isAuthenticated) {
      let jwtString = AuthStore.state.jwt;

      this.state.loading = true;
      this._changed();

      fetch(
        Endpoints["dashboardFetchRepoData"] + repoId, {
          method: 'GET',
          headers: {
            'Content-Type':'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + jwtString,
          },
        }
      ).then(response => {
        this._handleResponse(response, RepoDataActions.fetchRepoData);
      });
    }
  }

  onFetchRepoDataCompleted (repoData) {
    this.state.repoWasFound = true;
    this.state.repoData = repoData;
    this.state.loading = false;
    this._changed();
  }

  onFetchRepoDataFailed (errorObject) {
    this.state.repoWasFound = false;
    this.state.repoData = {};
    this.state.error = errorObject["Message"];
    this.state.loading = false;
    this._changed();
  }


  onCreateNewRepo(repoName, repoDescription) {
    if (AuthStore.state.isAuthenticated) {
      let jwtString = AuthStore.state.jwt;

      this.state.creationState.creating = true;
      this._changed();

      fetch(
        Endpoints["dashboardCreateNewRepo"], {
          method: 'POST',
          headers: {
            'Content-Type':'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + jwtString,
          },
          body: JSON.stringify({
            "RepoName": repoName,
            "RepoDescription": repoDescription,
          })
        }
      ).then(response => {
        this._handleResponse(response, RepoDataActions.createNewRepo);
      });
    }
  }

  onCreateNewRepoCompleted(results) {
    console.log(results)
    this.state.creationState.repoId = results["Results"]["RepoId"];
    this.state.creationState.apiKey = results["Results"]["TrueApiKey"];
    this.state.creationState.creating = false;
    this.state.creationState.created = true;
    this._changed();
  }

  onCreateNewRepoFailed(errorObject) {
    this.state.creationState.repoId = null;
    this.state.creationState.apiKey = null;
    this.state.creationState.creating = false;
    this.state.creationState.created = false;
    this.state.creationState.error = errorObject["Message"];
    this._changed();
  }


  onFetchReposRemaining() {
    if (AuthStore.state.isAuthenticated) {
      let jwtString = AuthStore.state.jwt;

      this.state.creationState.loading = true;
      this._changed();

      fetch(
        Endpoints["dashboardFetchReposRemaining"], {
          method: 'GET',
          headers: {
            'Content-Type':'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + jwtString,
          }
        }
      ).then(response => {
        this._handleResponse(response, RepoDataActions.fetchReposRemaining);
      });
    }
  }

  onFetchReposRemainingCompleted(results) {
    this.state.creationState.loading = false;
    this.state.creationState.reposRemaining = results["ReposRemaining"];
    this._changed();
  }

  onFetchReposRemainingFailed(errorObject) {
    this.state.creationState.loading = false;
    this.state.creationState.error = errorObject["Message"];
    this._changed();
  }

  onResetState() {
    this.init();
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

  _changed () {
    this.trigger(this.state);
  }

}

export default RepoDataStore;
