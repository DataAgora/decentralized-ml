import React from 'react';
import ReactDOM from 'react-dom';
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

import CoordinatorActions from './../actions/CoordinatorActions';


var username = null;
var repo_id = null;
var cachedElements = {}
var timerOn = {}

class Repo extends Reflux.Component {
  constructor(props) {
    super(props);
    this.stores = [RepoDataStore, RepoLogsStore];

    const { match: { params } } = this.props;
    this.repoId = params.repoId;
    repo_id = this.repoId
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
    let createdLessThan10MinutesAgo = Math.floor(Date.now()/1000) < (this.state.repoData.CreatedAt + 60*10) 
    if (AuthStore.state.isAuthenticated) {
      let jwtString = AuthStore.state.jwt;
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
        username = r["Message"];
        setUsername(username);
      });
    }
    RepoDataActions.fetchRepoData(repoId);
    RepoLogsActions.fetchRepoLogs(repoId);
    this.updateStatus = this.updateStatus.bind(this)
    if (!(repoId in timerOn && timerOn[repoId])) {
      setTimeout(this.updateStatus, 500)
    } else {
      console.log("manual update")
      console.log(cachedElements)
      setTimeout(this.update, 500, cachedElements[repoId])
    }
  }

  resetState() {
    if (AuthStore.state.isAuthenticated) {
      let jwtString = AuthStore.state.jwt;
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
        if (r["Error"] == false)
          window.location.href = '/dashboard';
      });
    }
  }

  copyRepoIDToClipboard() {
    let text = repo_id
    var dummy = document.createElement("textarea");
    // to avoid breaking orgain page when copying more words
    // cant copy when adding below this code
    // dummy.style.display = 'none'
    document.body.appendChild(dummy);
    //Be careful if you use texarea. setAttribute('value', value), which works with "input" does not work with "textarea". – Eduard
    dummy.value = text;
    dummy.select();
    document.execCommand("copy");
    document.body.removeChild(dummy);
  }

  copyUsernameToClipboard() {
    let text = username
    var dummy = document.createElement("textarea");
    // to avoid breaking orgain page when copying more words
    // cant copy when adding below this code
    // dummy.style.display = 'none'
    document.body.appendChild(dummy);
    //Be careful if you use texarea. setAttribute('value', value), which works with "input" does not work with "textarea". – Eduard
    dummy.value = text;
    dummy.select();
    document.execCommand("copy");
    document.body.removeChild(dummy);
  }

  copyRepoToClipboard() {
    let text = "https://github.com/DiscreetAI/decentralized-ml"
    var dummy = document.createElement("textarea");
    // to avoid breaking orgain page when copying more words
    // cant copy when adding below this code
    // dummy.style.display = 'none'
    document.body.appendChild(dummy);
    //Be careful if you use texarea. setAttribute('value', value), which works with "input" does not work with "textarea". – Eduard
    dummy.value = text;
    dummy.select();
    document.execCommand("copy");
    document.body.removeChild(dummy);
  }

  updateStatus() {
    console.log("update!", this)
    const { match: { params } } = this.props;
    const repoId = params.repoId;
    console.log(repoId)
    let jwtString = AuthStore.state.jwt;
    let createdLessThan10MinutesAgo = Math.floor(Date.now()/1000) < (this.state.repoData.CreatedAt + 60*10);

    fetch(
      Endpoints["dashboardFetchCoordinatorStatus"] + repoId, {
        method: 'GET',
        headers: {
          'Content-Type':'application/json',
          'Accept': 'application/json',
          'Authorization': 'Bearer ' + jwtString,
        },
      }
    ).then(response => response.json())
    .then(response => {
      let status = response
      var newEl = document.createElement('span');
      newEl.id = "status"
      if (status === undefined) {
        newEl.classList.add("badge")
        newEl.classList.add("badge-pill")
        newEl.classList.add("badge-dark")
        newEl.innerHTML = "..."
      }
  
      if (!("Busy" in status)) {
        console.log(Math.floor(Date.now()/1000), (this.state.repoData.CreatedAt + 60*10))
        if (createdLessThan10MinutesAgo) {
          newEl.classList.add("badge")
          newEl.classList.add("badge-pill")
          newEl.classList.add("badge-warning")
          newEl.innerHTML = "Deploying..."
        } else {
          newEl.classList.add("badge")
          newEl.classList.add("badge-pill")
          newEl.classList.add("badge-danger")
          newEl.innerHTML = "Unknown"
        }
      } else {
        if (status["Busy"] === true) {
          newEl.classList.add("badge")
          newEl.classList.add("badge-pill")
          newEl.classList.add("badge-success")
          newEl.innerHTML = "Active"
        } else {
          newEl.classList.add("badge")
          newEl.classList.add("badge-pill")
          newEl.classList.add("badge-secondary")
          newEl.innerHTML = "Idle"
        }
      }
      
      console.log(newEl)
      
      if (this.stillOnRepoPage(repoId)) {
        console.log("automatic update")
        this.update(newEl)
        cachedElements[repoId] = newEl.cloneNode(true);
        setTimeout(this.updateStatus, 20000)
        timerOn[repoId] = true;
      } else {
        timerOn[repoId] = false
      }
    });
  }

  update(newEl) {
    let object = document.getElementById("status")
    object.parentNode.replaceChild(newEl, object);
  }

  stillOnRepoPage(repoId) {
    let url = window.location.href.split('/')
    console.log(url.length == 5, url[3] == 'repo', url[4] == repoId, url)
    return url.length == 5 && url[3] == 'repo' && url[4] == repoId
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
            <span id="status"></span>
            <p className="mt-3"><button onClick={this.resetState} className="btn btn-xs btn-dark"><b>Reset</b></button></p>
            <p className="mt-3"><button onClick={this.deleteRepo} className="btn btn-xs btn-red-alt"><b>Delete Repo</b></button></p>
          </div>
        </div>
        <div className="row">
        <div className="col-1"></div>
          <div className="col-8">

            <p id="bigo">
              To start your training session, complete the following steps once the cloud node status is <b>Idle</b>.
              <br></br><br></br>
              <ol>
                <li>Click <a href={"https://explora.discreetai.com"}>here</a> to use Explora and start your session.</li>
                <br></br>
                <li>Sign in using just your Explora username:  <b id="username">{username}</b>.  <button class="btn btn-xs btn-primary ml-2" onClick={this.copyUsernameToClipboard}>Copy to Clipboard</button></li>
                <br></br>
                <li>Open a new terminal, and clone our Github repo <a href="https://github.com/DiscreetAI/decentralized-ml">here</a>. <button class="btn btn-xs btn-primary ml-2" onClick={this.copyRepoToClipboard}>Copy to Clipboard</button></li>
                <br></br>
                <li>Navigate to <i>decentralized-ml/explora</i>. Open the notebook <i>Explora.ipynb</i> for Javascript/Python sessions or the notebook <i>ExploraMobile.ipynb</i> for iOS sessions.</li>
                <br></br>
                <li>Fill in the repo ID cell (<code>repo_id = # REPO ID HERE</code>) with: <b>{this.state.repoData.Id}</b>.  <button class="btn btn-xs btn-primary ml-2" onClick={this.copyRepoIDToClipboard}>Copy to Clipboard</button> </li>
                <br></br>
                <li>Run the cells to begin training with the sample model!</li>
              </ol>
              </p>
          </div>
        </div>

        <RepoModels logs={this.state.repoLogs} />

      </div>
    )
  }
}

export default Repo;
