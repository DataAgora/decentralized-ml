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

import trackRepoStatus from "./../utils/updateStatus";


class Repo extends Reflux.Component {
  constructor(props) {
    super(props);
    this.stores = [RepoDataStore, RepoLogsStore];

    const { match: { params } } = this.props;
    this.repoId = params.repoId;
    this.resetState = this.resetState.bind(this);
    this.deleteRepo = this.deleteRepo.bind(this);
    this.exploraURL = "http://" + this.repoId + ".explora.discreetai.com"
  }

  async componentDidMount() {
    // const { match: { params } } = this.props;
    // const repoId = params.repoId;
    RepoDataActions.fetchRepoData(this.repoId);
    RepoLogsActions.fetchRepoLogs(this.repoId);
    trackRepoStatus(this.repoId, false)
  }

  resetState() {
    // const { match: { params } } = this.props;
    // const repoId = params.repoId;
    RepoDataActions.resetState(this.repoId);
  }

  deleteRepo() {
    // const { match: { params } } = this.props;
    // const repoId = params.repoId;
    RepoDataActions.deleteRepo(this.repoId);
  }

  copyRepoIDToClipboard() {
    // const { match: { params } } = this.props;
    // const repoId = params.repoId;
    var dummy = document.createElement("textarea");
    document.body.appendChild(dummy);
    dummy.value = this.repoId;
    dummy.select();
    document.execCommand("copy");
    document.body.removeChild(dummy);
  }

  render() {
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
            <RepoStatus repoId={this.state.repoData.Id} />
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
                <li>Click <a href={this.exploraURL}>here</a> to log in to Explora and start your session. Use your API key for the password.</li>
                <br></br>
                <li>Open the notebook <i>Explora.ipynb</i> for Javascript/Python sessions or the notebook <i>ExploraMobile.ipynb</i> for iOS sessions.</li>
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
