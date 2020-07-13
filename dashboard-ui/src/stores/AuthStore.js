import Reflux from 'reflux';
import cookie from 'react-cookies';
import AuthActions from './../actions/AuthActions';
import Endpoints from './../constants/endpoints.js';
import DashboardActions from './../actions/DashboardActions';


// TODO: Implement session keep-alive logic.
class AuthStore extends Reflux.Store {
  constructor () {
    super();
    this.init();
    this.listenables = AuthActions;
  }

  init () {
    if (!this._isAuthenticated()) {
      this._resetState();
    } else {
      // Pull cached token if one exists...
      this.state = {
        hasError: false,
        error: "",
        loading: false,
        jwt: this._getJWT(),
        claims: this._getClaims(),
        isAuthenticated: true,
        waiting: false,
        linkToDemo: false,
        demoRepoId: "",
      };
    }
  }

  onLogin (email, password) {
    this._resetState();
    this.state.loading = true;
    this.state.waiting = true;
    this._changed();

    var endpoint = Endpoints["authLogin"];
    fetch(
      endpoint, {
        method: 'POST',
        headers: {
          'Content-Type':'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({"username": email, "password": password}),
      }
    ).then(response => {
      this._handleLoginRegistrationResponse(response, AuthActions.login);
    });
  }

  onLoginCompleted (jwt) {
    this.state.jwt = jwt;
    this.state.waiting = false;
    localStorage.setItem('jwt', jwt);
    this.state.claims = this._getClaims();
    this.state.hasError = false;
    this.state.error = "";
    this.state.isAuthenticated = true;
    this.state.loading = false;
    console.log(this.state)
    this._deleteCookies();
    this._changed();
  }

  onLoginFailed (errorMessage) {
    this._resetState();
    let fullErrorMessage = "LOGIN ERROR: ";
    Object.values(errorMessage).forEach(function(list) {
      list.forEach(function(message) {
        fullErrorMessage += message + "\n";
      });
    });
    this.state.waiting = false;
    this.state.hasError = true;
    this.state.error = fullErrorMessage;
    this._changed();
  }

  onRegistration (registrationObject) {
    this._resetState();
    this.state.loading = true;
    this.state.waiting = true;
    this._changed();

    fetch(
      Endpoints["authRegistration"], {
        method: 'POST',
        headers: {
          'Content-Type':'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(registrationObject),
      }
    ).then(response => {
        
      this._handleLoginRegistrationResponse(response, AuthActions.registration);
    });
  }

  onRegistrationCompleted (message) {
    var demoRepoId = message["demo_repo_id"]
    this.state.claims = this._getClaims();
    this.state.hasError = false;
    this.state.error = "";
    this.state.waiting = false;
    this.state.isAuthenticated = true;
    this.state.loading = false;
    this.state.linkToDemo = true;
    this.state.demoRepoId = demoRepoId
    this.onLogin(message["username"], message["password"])
  }

  onRegistrationFailed(errorMessage) {
    this._resetState();
    let fullErrorMessage = "REGISTRATION ERROR: ";
    Object.values(errorMessage).forEach(function(list) {
      list.forEach(function(message) {
        fullErrorMessage += message + "\n";
      });
    });
    this.state.waiting = false;
    this.state.hasError = true;
    this.state.error = fullErrorMessage;
    this._changed();
  }

  onClearError() {
    this.state.error = "";
    this.state.hasError = false;
  }

  onLogout () {
    // Clear it all!
    this._resetState();
    this._changed();
  }

  _handleLoginRegistrationResponse(response, refluxAction) {
    response.json().then(serverResponse => {
      console.log(serverResponse)
      if ("access_token" in serverResponse) {
        refluxAction.completed(serverResponse["access_token"])
      } else if (serverResponse["error"]) {
        this._resetState();
        let errorMessage = serverResponse["message"];
        this.state.hasError = true;
        this.state.error = errorMessage;
        console.log(errorMessage);
        this._changed();
      } else if (serverResponse["message"] && "demo_repo_id" in serverResponse["message"]) {
        refluxAction.completed(serverResponse["message"]);
      } else {
        // TODO: Use error returned by server.
        refluxAction.failed(serverResponse["message"]);
      }
    });
  }

  _isAuthenticated () {
    return this._getJWT();
  }

  _getClaims() {
    var jwt = this._getJWT();
    if (jwt === null) {
      return null;
    }
    return JSON.parse(atob(jwt.split('.')[1]));
  }

  _getJWT() {
    var jwt = localStorage.getItem("jwt");
    if (!jwt) {
      return null;
    }
    return jwt;
  }

  _changed () {
    this.trigger(this.state);
  }

  _resetState () {
    this.state = {
      hasError: false,
      error: "",
      loading: false,
      jwt: null,
      isAuthenticated: false,
      claims: {},
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
      waiting: false,
      transition: true,
      linkToDemo: false,
    };

    localStorage.removeItem('jwt');

    this._deleteCookies();
  }

  _deleteCookies() {
    cookie.remove('csrftoken', { path: '/' });
    cookie.remove('sessionid', { path: '/' });
  }

}

export default AuthStore;
