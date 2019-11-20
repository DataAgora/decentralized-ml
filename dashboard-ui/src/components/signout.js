import React, { Component } from 'react';
import { Redirect } from 'react-router-dom';
import AuthActions from './../actions/AuthActions';


class SignOut extends Component {

  componentDidMount() {
    AuthActions.logout();
  }

  render() {
    return (
      <div>
        <Redirect to="/"/>
        Signing out...
      </div>
    );
  }
}

export default SignOut;
