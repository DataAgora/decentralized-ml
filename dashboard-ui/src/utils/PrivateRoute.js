import React from 'react';
import { Route, Redirect } from 'react-router-dom';
import AuthStore from './../stores/AuthStore';

const PrivateRoute = ({ component: Component, ...rest }) => (
  <Route
    {...rest}
    render={props =>
      AuthStore.state.isAuthenticated ? (
        <Component {...props} />
      ) : (
        <Redirect
          to={{
            pathname: "/signin",
            state: { from: props.location }
          }}
        />
      )
    }
  />
);

export default PrivateRoute;
