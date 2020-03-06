import Reflux from 'reflux';
import cookie from 'react-cookies';
import AuthActions from './../actions/AuthActions';
import Endpoints from './../constants/endpoints.js';


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
        error: false,
        loading: false,
        jwt: this._getJWT(),
        claims: this._getClaims(),
        isAuthenticated: true
      };
    }
  }

  onLogin (email, password) {
    this._resetState();
    this.state.loading = true;
    this._changed();

    var endpoint = Endpoints["eauthLogin"];
    fetch(
      endpoint, {
        method: 'POST',
        headers: {
          'Content-Type':'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({"email": email, "password": password}),
      }
    ).then(response => {
      this._handleLoginRegistrationResponse(response, AuthActions.login);
    });
  }

  onLoginCompleted (jwt) {
    this.state.jwt = jwt;
    localStorage.setItem('jwt', jwt);
    this.state.claims = this._getClaims();
    this.state.error = false;
    this.state.isAuthenticated = true;
    this.state.loading = false;
    this._deleteCookies();
    this._changed();
  }

  onLoginFailed (errorMessage) {
    this._resetState();
    this.state.error = errorMessage;
    this._changed();
  }

  onRegistration (registrationObject) {
    this._resetState();
    this.state.loading = true;
    this._changed();

    fetch(
      Endpoints["eauthRegistration"], {
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

  onRegistrationCompleted (jwt) {
    this.state.jwt = jwt;
    localStorage.setItem('jwt', jwt);
    this.state.claims = this._getClaims();
    this.state.error = false;
    this.state.isAuthenticated = true;
    this.state.loading = false;
    this._deleteCookies();
    this._changed();
  }

  onRegistrationFailed(errorMessage) {
    this._resetState();
    this.state.error = errorMessage;
    this._changed();
  }

  onLogout () {
    // Clear it all!
    this._resetState();
    this._changed();
  }

  _handleLoginRegistrationResponse(response, refluxAction) {
    response.json().then(serverResponse => {
      if (serverResponse && "token" in serverResponse) {
        var jwt = serverResponse['token'];
        refluxAction.completed(jwt);
      } else {
        // TODO: Use error returned by server.
        refluxAction.failed(JSON.stringify(serverResponse));
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
      error: false,
      loading: false,
      jwt: null,
      isAuthenticated: false,
      claims: {},
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
