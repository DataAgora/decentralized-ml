import React, { Component } from 'react';
import RepoList from './dashboard/repoList';
import AuthStore from './../stores/AuthStore';



class Dashboard extends Component {
  render() {
    if (AuthStore.state.linkToDemo) {
      this.props.history.push("/repo/" + AuthStore.state.demoRepoId)
      AuthStore.state.linkToDemo = false;
    }

    return (
      <div>
        <RepoList />
      </div>
    );
  }
}

export default Dashboard;
