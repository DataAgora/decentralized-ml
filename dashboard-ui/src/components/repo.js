import React from 'react';
import Reflux from 'reflux';

import NotFoundPage from './notFoundPage';
import RepoStatus from './repo/repoStatus';
import RepoLogs from './repo/repoLogs';
import RepoModels from './repo/repoModels';
import { Link } from 'react-router-dom';

import RepoDataStore from './../stores/RepoDataStore';
import RepoDataActions from './../actions/RepoDataActions';

import RepoLogsStore from './../stores/RepoLogsStore';
import RepoLogsActions from './../actions/RepoLogsActions';

import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';

import Endpoints from './../constants/endpoints.js';
import AuthStore from './../stores/AuthStore';

var username = null;
var repo_id = null;

class Repo extends Reflux.Component {
  constructor(props) {
    super(props);
    this.stores = [RepoDataStore, RepoLogsStore];

    const { match: { params } } = this.props;
    this.repoId = params.repoId;
    repo_id = this.repoId
    console.log("DONE");

  }

  setUsername(username) {
    try {
      document.getElementById("username").innerHTML = username
    } catch (e) {
      setTimeout(this.setUsername(username), 100)
    }
  }

  async componentDidMount() {
    const { match: { params } } = this.props;
    const repoId = params.repoId;
    var setUsername = this.setUsername;

    if (AuthStore.state.isAuthenticated) {
      let jwtString = AuthStore.state.jwt;
      console.log("component", jwtString)
      fetch(
        Endpoints["dashboardGetExploraURL"] + repo_id, {
          method: 'POST',
          dataType:'json',
          headers: {
            'Content-Type':'application/json',
            'Accept': 'application/json',
          },
          body: JSON.stringify({
            'token': jwtString
          })
        }
      )
      .then(r => r.json())
      .then(r => {
        console.log(r)
        username = r["Message"];
        console.log(username)
        setUsername(username);
      });
    }
    RepoDataActions.fetchRepoData(repoId);
    RepoLogsActions.fetchRepoLogs(repoId);
    
  }

  resetState() {
    if (AuthStore.state.isAuthenticated) {
      let jwtString = AuthStore.state.jwt;
      console.log(jwtString)
      fetch(
        Endpoints["dashboardResetCloudNode"] + repo_id, {
          method: 'POST',
          dataType:'json',
          headers: {
            'Content-Type':'application/json',
            'Accept': 'application/json',
          },
          body: JSON.stringify({
            'token': jwtString
          })
        }
      )
      .then(r => r.json())
      .then(r => {
        console.log(r)
      });
    }
  }

  deleteRepo() {
    if (AuthStore.state.isAuthenticated) {
      let jwtString = AuthStore.state.jwt;
      console.log("delete", jwtString)
      fetch(
        Endpoints["dashboardDeleteRepo"] + repo_id, {
          method: 'POST',
          dataType:'json',
          headers: {
            'Content-Type':'application/json',
            'Accept': 'application/json',
          },
          body: JSON.stringify({
            'token': jwtString
          })
        }
      )
      .then(r => r.json())
      .then(r => {
        console.log(r)
        if (r["Error"] == false)
          window.location.href = '/dashboard';
      });
    }
  }

  render() {
    // if (this.state.error !== false) {
    //   return (
    //     <div className="text-center"><p>
    //       Error: {this.state.error}</p>
    //     </div>
    //   );
    // }

    if (this.state.loading === true) {
      return (
        <div className="text-center text-secondary">
          <FontAwesomeIcon icon="sync" size="lg" spin />
        </div>
      );
    }

    if (!this.state.repoWasFound) {
      return <NotFoundPage />
    }
    let createdLessThan10MinutesAgo = Math.floor(Date.now()/1000) < (this.state.repoData.CreatedAt + 60*10);
    return (
      <div className="pb-5">
        <div className="row">
          <div className="col-1"></div>
          <div className="col-8">
            <h3>{this.state.repoData.Name}</h3>
            <p>{this.state.repoData.Description}</p>
          </div>
          <div className="col-2 text-right">
            <RepoStatus repoId={this.state.repoData.Id} isDeploying={createdLessThan10MinutesAgo} />
            <p className="mt-3"><button onClick={this.resetState} className="btn btn-xs btn-dark"><b>Reset</b></button></p>
            <p className="mt-3"><button onClick={this.deleteRepo} className="btn btn-xs btn-red-alt"><b>Delete Repo</b></button></p>
          </div>
        </div>
        <div className="row">
        <div className="col-1"></div>
          <div className="col-8">
            <p id="bigo">Click <a href={"https://explora.discreetai.com"}>here</a> to use Explora and start your session.
             <br></br>  <br></br>Sign in with the username <b id="username">{username}</b> and leave the password blank.
             <br></br>  <br></br>Open a new terminal, and clone <a href={"https://github.com/DiscreetAI/decentralized-ml"}>this GitHub repo</a>. Navigate to <i>decentralized-ml/explora</i>. Open the notebook <i>Explora.ipynb</i> for Javascript/Python sessions or the notebook <i>ExploraSample.ipynb</i> 
             <br></br> <br></br>Your repo ID is: <b> {this.state.repoData.Id} </b>.</p>
          </div>
        </div>

        <RepoModels logs={this.state.repoLogs} />

      </div>
    )
  }
}

export default Repo;
