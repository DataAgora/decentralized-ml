import React from 'react';
import ReactDOM from 'react-dom';
import Reflux from 'reflux';

import NotFoundPage from './notFoundPage';
import RepoStatus from './repo/repoStatus';
import LaunchStep from './repo/launchStep';
import RepoMetadata from './repo/repoMetadata';
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
    this.copyApiKeyToClipboard = this.copyApiKeyToClipboard.bind(this);
  }

  componentDidMount() {
    // const { match: { params } } = this.props;
    // const repoId = params.repoId;
    RepoDataActions.fetchRepoData(this.repoId);
    RepoLogsActions.fetchRepoLogs(this.repoId);
    trackRepoStatus(this.repoId, false)
  }

  copyApiKeyToClipboard() {
    // const { match: { params } } = this.props;
    // const repoId = params.repoId;
    var dummy = document.createElement("textarea");
    document.body.appendChild(dummy);
    dummy.value = this.state.repoData["ApiKey"];
    dummy.select();
    document.execCommand("copy");
    document.body.removeChild(dummy);
  }

  render() {
    let logs = this.state.repoLogs[this.repoId]

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
    
    return (
      <div className="pb-5">
        <RepoMetadata repoData={this.state.repoData}/>
       
        <div className="row">
        <div className="col-1"></div>
          <div className="col-8">

            <p id="bigo">
              <br></br><br></br>
              <h1>Getting Started</h1>
              <br></br>
              To start your training session, complete the following steps once the cloud node status is <b>Idle</b>.
              <br></br><br></br>
              <ol>
                <LaunchStep repoId={this.state.repoData.Id} isDemo={this.state.repoData.IsDemo}/>
                <br></br>
                <li>Enter the following API key as the password to Explora:</li>
                <br></br>
                <h6> <b>API KEY:  <span className="text-success">{ this.state.repoData.ApiKey }</span></b>   <button class="btn btn-xs btn-dark copy" onClick={this.copyApiKeyToClipboard}>Copy to Clipboard</button></h6>
                <br></br>
                <li>Run the cells to begin training with the sample model!</li>
              </ol>
              </p>
          </div>
        </div>

        <RepoModels logs={logs} repoId={this.state.repoData.Id} />

      </div>
    )
  }
}

export default Repo;
