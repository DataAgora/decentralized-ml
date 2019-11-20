import React from 'react';
import { Switch, Route } from 'react-router-dom';

import PrivateRoute from './utils/PrivateRoute';
import AuthRoute from './utils/AuthRoute';

import Home from './components/homePage';
import SignIn from './components/signin';
import SignUp from './components/signup';
import SignOut from './components/signout';
import Dashboard from './components/dashboard';
import Repo from './components/repo'
import NewRepo from './components/newRepo'
import NotFoundPage from './components/notFoundPage';


var Routes = () => (
  <Switch>
    <AuthRoute exact path="/" name="app" component={Home} />
    <AuthRoute path="/signin" name="signin" component={SignIn} />
    <AuthRoute path="/signup" name="signup" component={SignUp} />
    <Route path="/signout" name="signout" component={SignOut} />
    <PrivateRoute name="dashboard" path="/dashboard" component={Dashboard} />
    <PrivateRoute name="repo" path="/repo/:repoId" component={Repo} />
    <PrivateRoute name="new" path="/new" component={NewRepo} />
    <Route component={NotFoundPage} />
  </Switch>
);

export default Routes;
