import Reflux from 'reflux';
import DashboardActions from './../actions/DashboardActions';
import AuthStore from './AuthStore';
import Endpoints from './../constants/endpoints.js';


class DashboardStore extends Reflux.Store {

  constructor () {
    super();
    this.init();
    this.listenables = DashboardActions;
  }

  init () {
    this.state = {
      repos: [],
      loading: true,
      error: false,
      linkToDemo: false,
    };
  }

  onFetchAllRepos() {
    if (AuthStore.state.isAuthenticated) {
      let jwtString = AuthStore.state.jwt;

      this.state.loading = true;
      this._changed();

      fetch(
        Endpoints["dashboardFetchAllRepos"], {
          method: 'GET',
          headers: {
            'Content-Type':'application/json',
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + jwtString,
          },
        }
      ).then(response => {
        this._handleFetchAllReposResponse(response);
      });
    }
  }

  _handleFetchAllReposResponse(response) {
    response.json().then(serverResponse => {
      if (serverResponse["error"]) {
        DashboardActions.fetchAllRepos.failed(serverResponse["message"]);
      } else {
        DashboardActions.fetchAllRepos.completed(serverResponse["message"]);
      }
    });
  }

  onFetchAllReposCompleted (repoList) {
    this.state.repos = repoList;
    this.state.repos.sort((a,b) =>{
      if (a.Name < b.Name) return -1;
      if (a.Name > b.Name) return 1;
      return 0;
    });
    this.state.loading = false;
    this._changed();
  }

  onFetchAllReposFailed (error) {
    this.state.repos = {};
    this.state.error = error;
    console.log(error);
    this.state.loading = false;
    this._changed();
  }

  _changed () {
    this.trigger(this.state);
  }

}

export default DashboardStore;
