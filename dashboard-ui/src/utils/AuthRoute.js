import React from 'react';
import { Route, Redirect } from 'react-router-dom';
import AuthStore from './../stores/AuthStore';

const AuthRoute = ({ component: Component, ...rest }) => (
  <Route
    {...rest}
    render={props =>
      !AuthStore.state.isAuthenticated ? (
        <Component {...props} />
      ) : (
        <Redirect
          to={{
            pathname: "/dashboard",
            state: { from: props.location }
          }}
        />
      )
    }
  />
);

export default AuthRoute;
