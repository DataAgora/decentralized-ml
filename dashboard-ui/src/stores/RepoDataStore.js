import Reflux from 'reflux';
import RepoDataActions from './../actions/RepoDataActions';
import AuthStore from './AuthStore';
import Endpoints from './../constants/endpoints.js';
import trackRepoStatus from "./../utils/updateStatus";


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

  onFetchRepoDataFailed (error) {
    this.state.repoWasFound = false;
    this.state.repoData = {};
    this.state.error = error;
    console.log(error);
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
    this.state.creationState.repoId = results["RepoId"];
    this.state.creationState.apiKey = results["ApiKey"];
    this.state.creationState.creating = false;
    this.state.creationState.created = true;
    this._changed();
  }

  onCreateNewRepoFailed(error) {
    this.state.creationState.repoId = null;
    this.state.creationState.apiKey = null;
    this.state.creationState.creating = false;
    this.state.creationState.created = false;
    this.state.creationState.error = error;
    console.log(error);
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

  onFetchReposRemainingFailed(error) {
    this.state.creationState.loading = false;
    this.state.creationState.error = error
    console.log(error);
    this._changed();
  }

  onResetState(repoId) {
    if (AuthStore.state.isAuthenticated) {
      let jwtString = AuthStore.state.jwt;

      this.state.creationState.loading = true;
      this._changed();

      fetch(
        Endpoints["dashboardResetCloudNode"] + repoId, {
          method: 'POST',
          headers: {
            'Content-Type':'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + jwtString,
          }, 
          body: JSON.stringify({})
        }
      ).then(response => {
        this._handleResponse(response, RepoDataActions.resetState);
      });
    }
  }

  onResetStateCompleted(repoId) {
    this.state.creationState.loading = false;
    console.log(repoId + "'s state successfully reset!")
    this._changed();
  }

  onResetStateFailed(error) {
    this.state.creationState.loading = false;
    this.state.creationState.error = error
    console.log(error);
    this._changed();
  }
  
  onDeleteRepo(repoId) {
    if (AuthStore.state.isAuthenticated) {
      let jwtString = AuthStore.state.jwt;

      this.state.creationState.loading = true;
      this._changed();

      fetch(
        Endpoints["dashboardDeleteRepo"] + repoId, {
          method: 'POST',
          headers: {
            'Content-Type':'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + jwtString,
          },
          body: JSON.stringify({})
        }
      ).then(response => {
        this._handleResponse(response, RepoDataActions.deleteRepo);
      });
    }
  }

  onDeleteRepoCompleted(repoId) {
    this.state.creationState.loading = false;
    trackRepoStatus(repoId, true)
    window.location.href = '/dashboard';
    console.log(repoId + " successfully deleted!")
    this._changed();
  }

  onDeleteRepoFailed(error) {
    this.state.creationState.loading = false;
    this.state.creationState.error = error
    console.log(error);
    this._changed();
  }


  _handleResponse(response, refluxAction) {
    response.json().then(serverResponse => {
      if (serverResponse["error"]) {
        refluxAction.failed(serverResponse["message"]);
      } else {
        refluxAction.completed(serverResponse["message"]);
      }
    });
  }

  _changed () {
    this.trigger(this.state);
  }

}

export default RepoDataStore;
